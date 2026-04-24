#!/usr/bin/env python3
"""Assistant-facing wrapper for structured chess queries.

Takes a natural-language chess question and returns a compact human-readable answer
instead of raw JSON. Built for chat usage and fast manual invocation.
"""

from __future__ import annotations

import argparse
import io
from contextlib import redirect_stdout
from pathlib import Path

try:
    from query_engine import DB_PATH, QueryError, run_query
    from query_fuzzy import run_fuzzy_query
    _QUERY_IMPORT_ERROR = None
except ModuleNotFoundError as e:
    DB_PATH = Path("games.pgn")
    QueryError = ValueError
    run_query = None
    run_fuzzy_query = None
    _QUERY_IMPORT_ERROR = e

from query_nl import (
    build_exact_query,
    build_fuzzy_query,
    explain_parse,
    normalize_space,
    parse_prompt,
)


def require_query_runtime() -> None:
    if _QUERY_IMPORT_ERROR is not None:
        raise SystemExit(
            "python-chess is required for the structured query tools. Install dependencies first: pip install -r requirements.txt"
        )


def format_match(item: dict, idx: int) -> str:
    lines = []
    title = f"{idx}. {item.get('white', '?')} vs {item.get('black', '?')} ({item.get('result', '*')})"
    lines.append(title)
    if item.get("study"):
        lines.append(f"   Study: {item['study']}")
    if item.get("chapter"):
        lines.append(f"   Chapter: {item['chapter']}")
    if item.get("url"):
        lines.append(f"   URL: {item['url']}")

    matched_moves = item.get("matched_moves", [])
    if matched_moves:
        seq = []
        for move in matched_moves:
            dot = "." if move["turn"] == "white" else "..."
            seq.append(f"{move['move_number']}{dot} {move['san']}")
        lines.append(f"   Sequence: {' → '.join(seq)}")
    if item.get("occurrence_count", 1) > 1:
        lines.append(
            f"   Grouped occurrence: {item['occurrence_count']} contiguous hits from ply {item.get('occurrence_start_ply')} to {item.get('occurrence_end_ply')}"
        )

    reasons = item.get("reasons") or []
    if reasons:
        lines.append("   Why:")
        for reason in reasons[:4]:
            lines.append(f"   - {reason}")

    if item.get("score") is not None:
        lines.append(f"   Score: {item['score']:.2f}")
    if item.get("matched_optional"):
        labels = ", ".join(opt["label"] for opt in item["matched_optional"][:4])
        lines.append(f"   Optional hits: {labels}")
    if item.get("missed_optional"):
        labels = ", ".join(opt["label"] for opt in item["missed_optional"][:3])
        lines.append(f"   Missed optionals: {labels}")
    return "\n".join(lines)


def summarize(payload: dict, top_n: int = 5) -> str:
    parse = payload.get("parse", {})
    mode = payload.get("mode", "exact")
    returned = payload.get("returned", 0)
    scanned = payload.get("scanned_games", 0)
    results = payload.get("results", [])[:top_n]

    if payload.get("status") == "needs_clarification":
        return f"Need clarification: {payload.get('message', 'query is too vague')}"

    lines = []
    anchor_bits = []
    if parse.get("player"):
        anchor_bits.append(parse["player"])
    if parse.get("color"):
        anchor_bits.append(parse["color"])
    if parse.get("moves"):
        anchor_bits.append("moves " + " → ".join(parse["moves"]))
    if parse.get("square_facts"):
        facts = []
        for fact in parse["square_facts"]:
            c = fact.get("color", "any")
            facts.append(f"{c} {fact['piece']} on {fact['square']}")
        anchor_bits.append("facts " + ", ".join(facts))

    anchor_text = "; ".join(anchor_bits) if anchor_bits else "no explicit anchors"
    lines.append(f"Mode: {mode}. {returned} match(es) from {scanned} scanned games. Anchors: {anchor_text}.")

    if not results:
        lines.append("No matches found.")
        compiled = payload.get("compiled_query")
        if compiled:
            lines.append("Tip: relax a constraint or switch to fuzzy mode.")
        return "\n".join(lines)

    for idx, item in enumerate(results, 1):
        lines.append("")
        lines.append(format_match(item, idx))

    return "\n".join(lines)


def run_nl_query(text: str, db: str, mode: str, player: str | None, color: str | None, limit: int, context_window: int) -> dict:
    require_query_runtime()
    forced_mode = None if mode == "auto" else mode
    parsed = parse_prompt(text, mode=forced_mode, player=player, color=color)

    if parsed.clarification_needed:
        return {
            "status": "needs_clarification",
            "parse": explain_parse(parsed),
            "message": parsed.clarification_needed,
        }

    compiled = build_fuzzy_query(parsed, limit, context_window) if parsed.mode == "fuzzy" else build_exact_query(parsed, limit, context_window)

    try:
        if parsed.mode == "fuzzy":
            payload = run_fuzzy_query(compiled, path=db)
        else:
            payload = run_query(compiled, path=db)
            payload["mode"] = "exact"
    except QueryError as e:
        return {
            "status": "error",
            "message": str(e),
            "parse": explain_parse(parsed),
            "compiled_query": compiled,
        }

    payload["parse"] = explain_parse(parsed)
    payload["compiled_query"] = compiled
    return payload


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Assistant-facing natural-language chess search")
    p.add_argument("text", nargs="*", help="Natural-language chess question")
    p.add_argument("--db", default=str(DB_PATH), help="Path to the PGN corpus (default: ./games.pgn)")
    p.add_argument("--mode", choices=["auto", "exact", "fuzzy"], default="auto")
    p.add_argument("--player", help="Force player")
    p.add_argument("--color", choices=["white", "black"], help="Force color")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--context-window", type=int, default=2)
    p.add_argument("--json", action="store_true", help="Also print raw payload after summary")
    return p


def main() -> int:
    args = build_parser().parse_args()
    text = normalize_space(" ".join(args.text))
    if not text:
        raise SystemExit("Need a natural-language query.")

    payload = run_nl_query(text, db=args.db, mode=args.mode, player=args.player, color=args.color, limit=args.limit, context_window=args.context_window)
    print(summarize(payload, top_n=args.limit))
    if args.json:
        import json
        print()
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
