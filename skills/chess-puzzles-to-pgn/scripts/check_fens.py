#!/usr/bin/env python3
"""
Validate the structural correctness of a list of FENs.

USAGE:
    python check_fens.py <pgn_file>      # extract FENs from a PGN and check
    python check_fens.py --fen "<fen>"   # check a single FEN

Catches:
- Wrong number of fields in the FEN (must be 6)
- Wrong number of ranks (must be 8)
- Ranks that don't sum to 8 squares
- Invalid characters
- Missing or duplicate kings
- Kings on adjacent squares (illegal in chess)
- Bad side-to-move character

This is a structural check only. A FEN that passes here might still
disagree with the source diagram — measurement and visual verification
are what guarantee correctness. But a FEN that fails here cannot be
right, so always run this before shipping.
"""

import argparse
import re
import sys
from pathlib import Path


def check_fen(fen, label=""):
    """Return a list of error messages for the given FEN. Empty list = ok."""
    errors = []
    parts = fen.split()
    if len(parts) != 6:
        errors.append(f"FEN must have 6 fields, got {len(parts)}")
        return errors

    board, side, castling, ep, halfmove, fullmove = parts
    ranks = board.split("/")
    if len(ranks) != 8:
        errors.append(f"need 8 ranks, got {len(ranks)}")
        return errors

    # Build occupancy map: (file_idx, rank_idx_top_down) -> piece char
    squares = {}
    for i, rank_str in enumerate(ranks):
        f = 0
        for ch in rank_str:
            if ch.isdigit():
                f += int(ch)
            elif ch in "rnbqkpRNBQKP":
                if f >= 8:
                    errors.append(f"rank {8 - i}: overflow")
                    break
                squares[(f, i)] = ch
                f += 1
            else:
                errors.append(f"invalid char '{ch}' in rank {8 - i}")
        if f != 8:
            errors.append(f"rank {8 - i}: '{rank_str}' sums to {f}, need 8")

    if side not in ("w", "b"):
        errors.append(f"bad side-to-move: {side!r}")

    pieces_str = "".join(squares.values())
    if pieces_str.count("K") != 1:
        errors.append(f"need exactly 1 white king, got {pieces_str.count('K')}")
    if pieces_str.count("k") != 1:
        errors.append(f"need exactly 1 black king, got {pieces_str.count('k')}")

    wk = bk = None
    for sq, p in squares.items():
        if p == "K":
            wk = sq
        elif p == "k":
            bk = sq

    if wk and bk:
        df = abs(wk[0] - bk[0])
        dr = abs(wk[1] - bk[1])
        if df <= 1 and dr <= 1:
            wf, wr = wk[0], 8 - wk[1]
            bf, br = bk[0], 8 - bk[1]
            files = "abcdefgh"
            errors.append(
                f"kings adjacent: white at {files[wf]}{wr}, black at {files[bf]}{br}"
            )

    return errors


def extract_fens_from_pgn(pgn_text):
    """Return a list of (label, fen) pairs from a PGN file's content.

    Label is taken from the [Event] tag of the chapter containing the FEN.
    """
    out = []
    current_event = None
    for line in pgn_text.splitlines():
        m = re.match(r'^\[Event\s+"([^"]*)"\]\s*$', line)
        if m:
            current_event = m.group(1)
            continue
        m = re.match(r'^\[FEN\s+"([^"]*)"\]\s*$', line)
        if m:
            out.append((current_event or "(no event)", m.group(1)))
    return out


def main():
    parser = argparse.ArgumentParser(description="Structurally validate FENs.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("pgn_file", nargs="?", type=Path,
                       help="PGN file to scan for FENs.")
    group.add_argument("--fen", type=str, help="Check a single FEN string.")
    args = parser.parse_args()

    fens = []
    if args.fen:
        fens = [("(stdin)", args.fen)]
    else:
        if not args.pgn_file.exists():
            print(f"Error: {args.pgn_file} does not exist", file=sys.stderr)
            sys.exit(1)
        fens = extract_fens_from_pgn(args.pgn_file.read_text(encoding="utf-8"))
        if not fens:
            print("No FENs found in PGN", file=sys.stderr)
            sys.exit(1)

    print(f"Checking {len(fens)} positions...")
    fail = 0
    for label, fen in fens:
        errs = check_fen(fen, label)
        if errs:
            fail += 1
            print(f"FAIL  {label}")
            for e in errs:
                print(f"      - {e}")
            print(f"      FEN: {fen}")
        else:
            print(f"OK    {label}")
    print()
    print(f"Total: {len(fens)} positions, {fail} errors")
    sys.exit(0 if fail == 0 else 3)


if __name__ == "__main__":
    main()
