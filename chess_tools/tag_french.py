#!/usr/bin/env python3
"""
Tag French Defense games with thematic categories.

Input PGN is read from --db / OPENING_PGN_PATH (default: games.pgn in cwd).
Output JSON defaults to /tmp/french_data.json; override with --output or
OPENING_TAG_OUTPUT.  Pass the output path to generate_french_pdf.py (via
OPENING_GUIDE_INPUT) to build the cheat-sheet PDF.

IMPORTANT: Thematic tags are based on the OPENING PHASE (first 15 moves)
to avoid false positives from random middlegame/endgame moves.
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_pgn import load_games
from french_rules import classify_variation, tag_french_game
from french_opening_data import DEFAULT_PGN, DEFAULT_TAG_OUTPUT, MOVE_CUTOFF
from opening_tag_pipeline import count_tags, tag_game_collection, write_tag_output

PGN = os.environ.get('OPENING_PGN_PATH', str(DEFAULT_PGN))
OUTPUT_JSON = os.environ.get('OPENING_TAG_OUTPUT', str(DEFAULT_TAG_OUTPUT))






def run(pgn_path=PGN, output_json=OUTPUT_JSON, quiet=False):
    _, french_games = load_games(pgn_path, 'sterkurstrakur')

    # Tag all games
    def _postprocess(game, raw):
        game['variation'] = classify_variation(game, raw)

    tag_game_collection(french_games, pgn_path, tag_french_game, postprocess=_postprocess)

    # Output stats
    if not quiet:
        print(f"Tagged {len(french_games)} French games")

    tags = count_tags(french_games)
    if not quiet:
        print("\nAll tags:")
        for t, c in sorted(tags.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c}")

    # Variation breakdown
    from collections import Counter
    vars_count = Counter(g['variation'] for g in french_games)
    if not quiet:
        print("\nVariations:")
        for v, c in vars_count.most_common():
            print(f"  {v}: {c}")

    # Write JSON
    data = {'games': french_games}
    write_tag_output(data, output_json, quiet=quiet)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Tag French Defense games with thematic categories.')
    parser.add_argument('--db', default=PGN, help='Path to PGN database')
    parser.add_argument('--output', default=OUTPUT_JSON, help='Path to output JSON')
    parser.add_argument('--quiet', action='store_true', help='Reduce stats output')
    args = parser.parse_args(argv)
    run(pgn_path=args.db, output_json=args.output, quiet=args.quiet)


if __name__ == '__main__':
    main()
