#!/usr/bin/env python3
"""Search chess-db for games matching a move prefix."""

import sys
import os
import chess.pgn

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "games.pgn")


def normalize_san(move: str) -> str:
    """Strip common annotations from a SAN move."""
    return move.rstrip("!?#")


def load_games(path: str):
    """Yield (game_number, headers, mainline_sans) for each game."""
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


def search(query_moves: list[str], path: str = DB_PATH):
    """Find games whose mainline starts with query_moves."""
    # Normalize query
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


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 search.py <move1> <move2> ...")
        print("Example: python3 search.py d4 d5 e3 Nc6")
        sys.exit(1)

    query = sys.argv[1:]
    matches = search(query)

    if not matches:
        print(f'No games match "{format_query(query)}"')
        sys.exit(0)

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


if __name__ == "__main__":
    main()
