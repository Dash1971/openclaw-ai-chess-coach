#!/usr/bin/env python3
"""Search a PGN corpus for games matching a move prefix."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().with_name("games.pgn")


def normalize_san(move: str) -> str:
    """Strip common annotations from a SAN move."""
    return move.rstrip("!?#")


def load_games(path: str):
    """Yield (game_number, headers, mainline_sans, study_name) for each game."""
    try:
        import chess.pgn  # type: ignore
    except ModuleNotFoundError as e:
        raise SystemExit(
            "python-chess is required for search.py. Install dependencies first: pip install -r requirements.txt"
        ) from e

    with open(path) as f:
        num = 0
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            num += 1
            board = game.board()
            sans = []
            for m in game.mainline_moves():
                sans.append(board.san(m))
                board.push(m)
            study = game.headers.get("StudyName", "Unknown Study")
            yield num, game.headers, sans, study


def search(query_moves: list[str], path: str = str(DEFAULT_DB_PATH)):
    """Find games whose mainline starts with query_moves."""
    query = [normalize_san(m) for m in query_moves]
    n = len(query)
    matches = []

    for num, headers, sans, study in load_games(path):
        if len(sans) < n:
            continue
        if [normalize_san(s) for s in sans[:n]] == query:
            matches.append((num, headers, study))

    return matches


def format_query(moves: list[str]) -> str:
    """Format moves as numbered pairs: 1. d4 d5 2. e3 Nc6"""
    parts = []
    for i, m in enumerate(moves):
        if i % 2 == 0:
            parts.append(f"{i // 2 + 1}.")
        parts.append(m)
    return " ".join(parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search a PGN corpus by opening move prefix.")
    parser.add_argument("moves", nargs="+", help="SAN moves to match from the start of the main line")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="Path to the PGN corpus (defaults to chess_tools/games.pgn if present)",
    )
    return parser


def main(argv: list[str] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"PGN database not found: {db_path}")

    query = args.moves
    matches = search(query, path=str(db_path))

    if not matches:
        print(f'No games match "{format_query(query)}"')
        return 0

    label = "game" if len(matches) == 1 else "games"
    print(f'{len(matches)} {label} match "{format_query(query)}":\n')

    for num, h, study in matches:
        white = h.get("White", "?")
        black = h.get("Black", "?")
        result = h.get("Result", "*")
        chapter = h.get("ChapterName", "")
        url = h.get("ChapterURL", "")
        print(f"  #{num:<4} {white} vs {black} ({result})")
        print(f"        Study: {study}")
        if chapter:
            print(f"        Chapter: {chapter}")
        if url:
            print(f"        {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
