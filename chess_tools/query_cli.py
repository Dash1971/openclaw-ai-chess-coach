#!/usr/bin/env python3
"""CLI wrapper for the structured chess query engine."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from query_engine import DB_PATH, QueryError, load_query, run_query
    from query_fuzzy import compile_fuzzy_to_exact, run_fuzzy_query
    _QUERY_IMPORT_ERROR = None
except ModuleNotFoundError as e:
    DB_PATH = Path("games.pgn")
    QueryError = ValueError
    load_query = None
    run_query = None
    compile_fuzzy_to_exact = None
    run_fuzzy_query = None
    _QUERY_IMPORT_ERROR = e


def require_query_runtime() -> None:
    if _QUERY_IMPORT_ERROR is not None:
        raise SystemExit(
            "python-chess is required for the structured query tools. Install dependencies first: pip install -r requirements.txt"
        )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Structured motif/position search over a PGN corpus")
    p.add_argument("--db", default=str(DB_PATH), help="Path to the PGN corpus (default: ./games.pgn)")
    p.add_argument("--query-file", help="Path to exact JSON query file")
    p.add_argument("--query-json", help="Inline exact JSON query")
    p.add_argument("--fuzzy-file", help="Path to fuzzy JSON query file")
    p.add_argument("--fuzzy-json", help="Inline fuzzy JSON query")
    p.add_argument("--compile-only", action="store_true", help="For fuzzy queries, print the compiled exact query without executing it")
    p.add_argument("--pretty", action="store_true", help="Pretty-print human summary as well as JSON")
    p.add_argument("--indent", type=int, default=2, help="JSON indent")
    return p


def pretty_print(payload: dict) -> None:
    results = payload.get("results", [])
    mode = payload.get("mode", "exact")
    print(f"{payload.get('returned', 0)} result(s) from {payload.get('scanned_games', 0)} scanned game(s) [{mode}]\n")
    for idx, item in enumerate(results, 1):
        print(f"{idx}. {item['white']} vs {item['black']} ({item['result']})")
        if item.get("study"):
            print(f"   Study: {item['study']}")
        if item.get("chapter"):
            print(f"   Chapter: {item['chapter']}")
        if item.get("url"):
            print(f"   URL: {item['url']}")
        if "score" in item:
            print(f"   Score: {item['score']:.2f}")
        print("   Matched sequence:")
        for move in item.get("matched_moves", []):
            dot = "." if move["turn"] == "white" else "..."
            print(f"     {move['move_number']}{dot} {move['san']} (ply {move['ply']})")
        if item.get("reasons"):
            print("   Reasons:")
            for reason in item["reasons"]:
                print(f"     - {reason}")
        if item.get("matched_optional"):
            print("   Optional hits:")
            for opt in item["matched_optional"]:
                print(f"     + {opt['label']} (weight {opt['weight']}, ply {opt['ply']}, {opt['san']})")
        if item.get("missed_optional"):
            print("   Optional misses:")
            for opt in item["missed_optional"]:
                print(f"     - {opt['label']} (weight {opt['weight']})")
        print()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    require_query_runtime()
    try:
        has_exact = bool(args.query_file or args.query_json)
        has_fuzzy = bool(args.fuzzy_file or args.fuzzy_json)
        if has_exact and has_fuzzy:
            raise QueryError("Use either exact query input or fuzzy query input, not both")
        if not has_exact and not has_fuzzy:
            raise QueryError("Provide --query-file/--query-json or --fuzzy-file/--fuzzy-json")

        if has_fuzzy:
            fuzzy = load_query(path=args.fuzzy_file, inline_json=args.fuzzy_json)
            if args.compile_only:
                payload = {
                    "mode": "compile-only",
                    "fuzzy_query": fuzzy,
                    "compiled_exact_query": compile_fuzzy_to_exact(fuzzy),
                }
            else:
                payload = run_fuzzy_query(fuzzy, path=os.path.abspath(args.db))
        else:
            query = load_query(path=args.query_file, inline_json=args.query_json)
            payload = run_query(query, path=os.path.abspath(args.db))
    except QueryError as e:
        print(f"Query error: {e}", file=sys.stderr)
        return 2

    if args.pretty:
        pretty_print(payload)
    print(json.dumps(payload, indent=args.indent, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
