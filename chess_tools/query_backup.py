#!/usr/bin/env python3
"""Procedural backup wrapper for structured chess queries.

Purpose:
- reduce model discretion for backup models like Kimi
- force a consistent ladder: parse -> compile -> run -> fallback -> summarize
- return a compact result with interpretation + best link when available
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from query_answer import run_nl_query, summarize
from query_nl import normalize_space, parse_prompt

try:
    from query_engine import run_query
    from query_fuzzy import run_fuzzy_query
    _QUERY_IMPORT_ERROR = None
except ModuleNotFoundError as e:
    run_query = None
    run_fuzzy_query = None
    _QUERY_IMPORT_ERROR = e


def require_query_runtime() -> None:
    if _QUERY_IMPORT_ERROR is not None:
        raise SystemExit(
            "python-chess is required for the structured query tools. Install dependencies first: pip install -r requirements.txt"
        )


def best_link(payload: dict[str, Any]) -> str | None:
    for item in payload.get("results", []):
        if item.get("url"):
            return item["url"]
    return None


def compact_interpretation(payload: dict[str, Any]) -> str:
    parse = payload.get("parse", {})
    bits: list[str] = []
    if payload.get("backup_normalized_text") and payload.get("backup_normalized_text") != parse.get("raw_text"):
        bits.append(f"normalized='{payload['backup_normalized_text']}'")
    if parse.get("mode"):
        bits.append(f"mode={parse['mode']}")
    if parse.get("player"):
        bits.append(f"player={parse['player']}")
    if parse.get("color"):
        bits.append(f"color={parse['color']}")
    if parse.get("filters"):
        bits.append(f"filters={parse['filters']}")
    if parse.get("moves"):
        bits.append(f"moves={parse['moves']}")
    if parse.get("square_facts"):
        bits.append(f"square_facts={parse['square_facts']}")
    motifs = parse.get("motif_templates") or []
    if motifs:
        labels = [m.get("label", "motif") for m in motifs[:5]]
        bits.append(f"motifs={labels}")
    return "; ".join(bits) if bits else "no explicit interpretation"


def normalize_backup_text(text: str) -> tuple[str, list[str]]:
    normalized = normalize_space(text)
    rules_applied: list[str] = []

    replacements = [
        (
            r"\brook\s+uplift(?:ed)?\b|\buplifted\s+rook\b|\brook\s+lifted\b",
            "rook lift",
            "rook uplift/uplifted/lifted rook → rook lift",
        ),
        (
            r"\b(?:queen\s*\+\s*rook|queen[-\s]?rook|rook[-\s]?queen|heavy[-\s]?piece)\s+battery\b",
            "queen-rook battery",
            "queen+rook/queen-rook/heavy-piece battery → queen-rook battery",
        ),
        (
            r"\b(?:leading|resulting|which resulted)\s+to\s+(?:a\s+)?checkmate\b|\bleading\s+to\s+(?:a\s+)?mate\b|\bmating\s+finish\b|\bmate\s+finish\b|\bcheckmating\s+finish\b",
            "mate finish",
            "leading to checkmate/mate/mating finish → mate finish",
        ),
    ]

    for pattern, repl, note in replacements:
        updated = re.sub(pattern, repl, normalized, flags=re.IGNORECASE)
        if updated != normalized:
            normalized = updated
            rules_applied.append(note)

    return normalize_space(normalized), rules_applied



def build_attack_shape_query(text: str, limit: int, context_window: int, *, fuzzy: bool) -> dict[str, Any] | None:
    low = text.lower()
    has_rook_lift = "rook lift" in low
    has_queen_rook_battery = "queen-rook battery" in low
    has_mate_finish = "mate finish" in low or bool(re.search(r"\bcheckmate\b|\bmate\b", low))

    if not (has_rook_lift and has_queen_rook_battery and has_mate_finish):
        return None

    sequence: list[dict[str, Any]] = [
        {
            "label": "rook lift",
            "move_by": "any",
            "predicates": [
                {
                    "type": "rook_lifted",
                    "phase": "before",
                    "color": "any",
                    "min_advance": 2,
                }
            ],
        },
        {
            "label": "queen-rook battery",
            "move_by": "any",
            "within_plies": 12,
            "predicates": [
                {
                    "type": "battery",
                    "phase": "before",
                    "color": "any",
                    "back_piece": "Q",
                    "front_piece": "R",
                }
            ],
        },
        {
            "label": "mate finish",
            "move": r".*#",
            "move_mode": "regex",
            "move_by": "any",
            "within_plies": 12,
        },
    ]

    if not fuzzy:
        return {
            "sequence": sequence,
            "limit": limit,
            "context_window": context_window,
        }

    return {
        "sequence": [
            {**sequence[0], "required": True},
            {**sequence[1], "required": False, "weight": 3.0},
            {**sequence[2], "required": True},
        ],
        "limit": limit,
        "context_window": context_window,
    }



def run_attack_shape_fallback(text: str, db: str, limit: int, context_window: int) -> dict[str, Any] | None:
    exact_query = build_attack_shape_query(text, limit, context_window, fuzzy=False)
    if not exact_query:
        return None

    exact = run_query(exact_query, path=db)
    exact["mode"] = "exact"
    exact["parse"] = {
        "raw_text": text,
        "mode": "exact",
        "player": None,
        "color": None,
        "filters": {},
        "moves": [],
        "square_facts": [],
        "motif_templates": [
            {"label": "rook lift"},
            {"label": "queen-rook battery"},
        ],
        "sequence_templates": [{"label": "rook lift -> queen-rook battery -> mate finish"}],
        "clarification_needed": None,
    }
    exact["compiled_query"] = exact_query
    exact["backup_interpretation_rules"] = [
        "treat rook uplift / rook uplifted as rook lift",
        "treat queen+rook / queen-rook / heavy-piece battery as queen-rook battery",
        "treat leading to checkmate / mate / mating finish as a later move matching #",
    ]
    if exact.get("returned", 0) > 0:
        exact["backup_stage"] = "attack-shape-exact"
        return exact

    fuzzy_query = build_attack_shape_query(text, limit, context_window, fuzzy=True)
    fuzzy = run_fuzzy_query(fuzzy_query, path=db)
    fuzzy["mode"] = "fuzzy"
    fuzzy["parse"] = exact["parse"]
    fuzzy["compiled_query"] = fuzzy_query
    fuzzy["backup_interpretation_rules"] = exact["backup_interpretation_rules"]
    if fuzzy.get("returned", 0) > 0:
        fuzzy["backup_stage"] = "attack-shape-fuzzy"
        return fuzzy

    return None



def procedural_search(text: str, db: str, limit: int, context_window: int) -> dict[str, Any]:
    require_query_runtime()
    normalized_text, rules_applied = normalize_backup_text(text)

    attack_shape = run_attack_shape_fallback(normalized_text, db=db, limit=limit, context_window=context_window)
     
    first = run_nl_query(normalized_text, db=db, mode="auto", player=None, color=None, limit=limit, context_window=context_window)
    if rules_applied:
        first["backup_normalized_text"] = normalized_text
        first["backup_normalization_rules"] = rules_applied

    if attack_shape:
        if rules_applied:
            attack_shape["backup_normalized_text"] = normalized_text
            attack_shape["backup_normalization_rules"] = rules_applied
        return attack_shape

    if first.get("status") not in {"needs_clarification", "error"} and first.get("returned", 0) > 0:
        first["backup_stage"] = "initial"
        return first

    if attack_shape:
        if rules_applied:
            attack_shape["backup_normalized_text"] = normalized_text
            attack_shape["backup_normalization_rules"] = rules_applied
        return attack_shape

    if first.get("status") in {"needs_clarification", "error"}:
        first["backup_stage"] = "initial"
        return first

    # Fallback 1: force fuzzy if initial auto/exact path produced nothing.
    fuzzy = run_nl_query(normalized_text, db=db, mode="fuzzy", player=None, color=None, limit=limit, context_window=context_window)
    if rules_applied:
        fuzzy["backup_normalized_text"] = normalized_text
        fuzzy["backup_normalization_rules"] = rules_applied
    if fuzzy.get("status") not in {"needs_clarification", "error"} and fuzzy.get("returned", 0) > 0:
        fuzzy["backup_stage"] = "forced-fuzzy"
        return fuzzy

    # Fallback 2: keep best diagnostic payload so backup models can restate interpretation.
    parsed = parse_prompt(normalized_text)
    return {
        "status": "no_matches",
        "message": "No matches found through the procedural backup ladder.",
        "backup_stage": "diagnostic",
        "backup_normalized_text": normalized_text,
        "backup_normalization_rules": rules_applied,
        "parse": {
            "raw_text": parsed.raw_text,
            "mode": parsed.mode,
            "player": parsed.player,
            "color": parsed.color,
            "filters": parsed.filters,
            "moves": parsed.moves,
            "square_facts": parsed.square_facts,
            "motif_templates": parsed.motif_templates,
            "clarification_needed": parsed.clarification_needed,
        },
        "initial": first,
        "forced_fuzzy": fuzzy,
    }


def render_backup_answer(payload: dict[str, Any], top_n: int) -> str:
    if payload.get("status") == "needs_clarification":
        return f"Need clarification: {payload.get('message')}"
    if payload.get("status") == "error":
        return f"Search error: {payload.get('message')}"
    if payload.get("status") == "no_matches":
        interpretation = compact_interpretation(payload)
        return (
            f"No matches found. Interpretation used: {interpretation}. "
            f"Best next move: restate the query with one anchor move, target square, or follow-up move."
        )

    rules = payload.get("backup_normalization_rules") or payload.get("backup_interpretation_rules") or []

    lines = []
    lines.append(f"Backup stage: {payload.get('backup_stage', 'initial')}")
    lines.append(f"Interpretation: {compact_interpretation(payload)}")
    if rules:
        lines.append(f"Rules: {'; '.join(rules)}")
    link = best_link(payload)
    if link:
        lines.append(f"Best link: {link}")
    lines.append("")
    lines.append(summarize(payload, top_n=top_n))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Procedural backup wrapper for structured chess queries")
    p.add_argument("text", nargs="*", help="Natural-language chess question")
    p.add_argument("--db", default="games.pgn", help="Path to the PGN corpus (default: ./games.pgn)")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--context-window", type=int, default=2)
    p.add_argument("--json", action="store_true", help="Also print raw JSON payload")
    return p


def main() -> int:
    args = build_parser().parse_args()
    text = normalize_space(" ".join(args.text))
    if not text:
        raise SystemExit("Need a natural-language query.")

    payload = procedural_search(text, db=args.db, limit=args.limit, context_window=args.context_window)
    print(render_backup_answer(payload, top_n=args.limit))
    if args.json:
        print()
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
