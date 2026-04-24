#!/usr/bin/env python3
r"""Proper PGN parser for arbitrary user-supplied corpora.

DO NOT use simple regex like re.findall(r'(\d+)\.\s*(\S+)\s+(\S+)', text)
for PGN parsing — it fails on annotations, variations, and continuations,
silently undercounting Black moves by 50%+. (Bug: 2026-03-08)

Usage:
    from parse_pgn import load_games
    white_games, black_games = load_games('games.pgn', player='wonestall')
"""

import argparse
import re
from pathlib import Path


def parse_moves(moves_text):
    """Parse PGN move text into (move_number, move) lists for white and black."""
    clean = re.sub(r'\{[^}]*\}', '', moves_text)   # strip comments
    clean = re.sub(r'\$\d+', '', clean)              # strip NAGs
    # Remove variations (nested parens) — flatten to main line
    while '(' in clean:
        clean = re.sub(r'\([^()]*\)', '', clean)

    tokens = clean.split()
    white_moves = []
    black_moves = []
    current_move = 0
    expecting = 'number_or_white'

    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        if tok in ('1-0', '0-1', '1/2-1/2', '*'):
            break

        # Move number: "12."
        num_match = re.match(r'^(\d+)\.$', tok)
        if num_match:
            current_move = int(num_match.group(1))
            expecting = 'white'
            continue

        # Continuation dots: "12..."
        if re.match(r'^\d+\.\.\.', tok):
            m = re.match(r'^(\d+)', tok)
            if m:
                current_move = int(m.group(1))
            expecting = 'black'
            continue

        # Actual move token
        if re.match(r'^[A-Za-z]', tok) or tok in ('O-O', 'O-O-O'):
            if expecting in ('white', 'number_or_white'):
                white_moves.append((current_move, tok))
                expecting = 'black'
            elif expecting == 'black':
                black_moves.append((current_move, tok))
                expecting = 'number_or_white'

    return white_moves, black_moves


def parse_game(game_text):
    """Parse a single PGN game into headers + white/black move lists."""
    headers = {}
    for m in re.finditer(r'\[(\w+) "([^"]*)"\]', game_text):
        headers[m.group(1)] = m.group(2)

    parts = game_text.split('\n\n')
    moves_text = parts[-1] if len(parts) > 1 else ''
    white_moves, black_moves = parse_moves(moves_text)

    return {
        'headers': headers,
        'wm': white_moves,
        'bm': black_moves,
        'white': headers.get('White', ''),
        'black': headers.get('Black', ''),
        'result': headers.get('Result', '*'),
        'url': headers.get('ChapterURL', ''),
        'chapter': headers.get('ChapterName', ''),
        'study': headers.get('StudyName', ''),
        'total': max(len(white_moves), len(black_moves)),
    }


def load_games(pgn_path, player=None):
    """Load all games from a PGN file. Optionally filter by player name.
    
    Returns (white_games, black_games) where the player has that color.
    If player is None, returns (all_games, []).
    """
    with open(pgn_path) as f:
        content = f.read()

    raw = re.split(r'\n\n(?=\[Event)', content)
    all_games = [parse_game(g) for g in raw if g.strip()]

    if player is None:
        return all_games, []

    player_lower = player.lower()
    white_games = [g for g in all_games if player_lower in g['white'].lower()]
    black_games = [g for g in all_games if player_lower in g['black'].lower()]
    return white_games, black_games


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Parse a PGN corpus with the proper non-regex parser.')
    parser.add_argument('pgn', nargs='?', default='games.pgn', help='Path to the PGN corpus (default: ./games.pgn)')
    parser.add_argument('--player', default='wonestall', help='Optional player filter (default: wonestall)')
    return parser


if __name__ == '__main__':
    args = build_parser().parse_args()
    wg, bg = load_games(args.pgn, args.player)
    print(f'Loaded {len(wg)} white + {len(bg)} black games for {args.player}')
