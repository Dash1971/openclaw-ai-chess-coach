#!/usr/bin/env python3
"""Run a few canned structured-query examples against a user-supplied PGN corpus."""

import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DEFAULT_PGN = Path('games.pgn')
sys.path.insert(0, str(BASE))

try:
    from query_engine import run_query, QueryError
    _QUERY_IMPORT_ERROR = None
except ModuleNotFoundError as e:
    run_query = None
    QueryError = ValueError
    _QUERY_IMPORT_ERROR = e


def require_query_runtime() -> None:
    if _QUERY_IMPORT_ERROR is not None:
        raise SystemExit(
            "python-chess is required for the structured query tools. Install dependencies first: pip install -r requirements.txt"
        )

# Query 1: Rook lift -> Queen-Rook battery -> checkmate
query1 = {
    "limit": 10,
    "context_window": 3,
    "sequence": [
        {
            "move_by": "any",
            "predicates": [
                {
                    "type": "rook_lifted",
                    "phase": "before",
                    "color": "any",
                    "min_advance": 2
                }
            ]
        },
        {
            "move_by": "any",
            "within_plies": 10,
            "predicates": [
                {
                    "type": "battery",
                    "phase": "after",
                    "color": "any",
                    "back_piece": "Q",
                    "front_piece": "R"
                }
            ]
        },
        {
            "move": ".*#",
            "move_mode": "regex",
            "move_by": "any",
            "within_plies": 8
        }
    ]
}


# Query 2: Simpler - just Q-R battery on h-file
query2 = {
    "limit": 10,
    "context_window": 3,
    "sequence": [
        {
            "move_by": "any",
            "predicates": [
                {
                    "type": "battery",
                    "phase": "before",
                    "color": "any",
                    "back_piece": "Q",
                    "front_piece": "R"
                }
            ]
        },
        {
            "move": ".*#",
            "move_mode": "regex",
            "move_by": "any",
            "within_plies": 4
        }
    ]
}


# Query 3: Rook lift followed by heavy pieces bringing mate
query3 = {
    "limit": 10,
    "context_window": 4,
    "sequence": [
        {
            "move_by": "any",
            "predicates": [
                {
                    "type": "rook_lifted",
                    "phase": "before",
                    "color": "any",
                    "min_advance": 2
                }
            ]
        },
        {
            "move": ".*#",
            "move_mode": "regex",
            "move_by": "any",
            "within_plies": 16
        }
    ]
}

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Run canned structured-query examples against a PGN corpus.')
    parser.add_argument('--db', default=str(DEFAULT_PGN), help='Path to the PGN corpus (default: ./games.pgn)')
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    db_path = args.db
    require_query_runtime()

    print("=" * 60)
    print("QUERY 1: Rook lift -> Q-R battery -> checkmate")
    print("=" * 60)

    try:
        result1 = run_query(query1, path=str(db_path))
        print(f"Scanned games: {result1['scanned_games']}, Matches: {result1['returned']}")
        for r in result1['results']:
            print(f"\n{result1['results'].index(r)+1}. {r['study']} - {r['chapter']}")
            print(f"   URL: {r['url']}")
            print(f"   Moves: {' -> '.join([m['san'] for m in r['matched_moves']])}")
            print(f"   Why: {r['reasons']}")
    except QueryError as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("QUERY 2: Q-R battery (anywhere) -> checkmate")
    print("=" * 60)

    try:
        result2 = run_query(query2, path=str(db_path))
        print(f"Scanned games: {result2['scanned_games']}, Matches: {result2['returned']}")
        for r in result2['results']:
            print(f"\n{result2['results'].index(r)+1}. {r['study']} - {r['chapter']}")
            print(f"   URL: {r['url']}")
            print(f"   Moves: {' -> '.join([m['san'] for m in r['matched_moves']])}")
            print(f"   Why: {r['reasons']}")
    except QueryError as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("QUERY 3: Rook lift -> checkmate (within 8 moves)")
    print("=" * 60)

    try:
        result3 = run_query(query3, path=str(db_path))
        print(f"Scanned games: {result3['scanned_games']}, Matches: {result3['returned']}")
        for r in result3['results']:
            print(f"\n{result3['results'].index(r)+1}. {r['study']} - {r['chapter']}")
            print(f"   URL: {r['url']}")
            print(f"   Moves: {' -> '.join([m['san'] for m in r['matched_moves']])}")
            print(f"   Why: {r['reasons']}")
    except QueryError as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
