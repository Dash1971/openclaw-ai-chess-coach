#!/usr/bin/env python3
"""
Detect occupied squares on a chess diagram by measuring ink density per square.

USAGE:
    python detect_occupancy.py <crop.jpg>
    python detect_occupancy.py <crop.jpg> --threshold 350 --inner 0.6

The crop must be a tight image of a single chess board with rank labels (1-8)
on the left and file labels (a-h) on the bottom both visible. The script
locates the board by detecting the long dark border lines, divides into 64
squares, and reports ink density (count of dark pixels) per square.

A square with a piece typically has ink density 600-2000+; an empty square
has 100-400 from board shading texture. The default threshold 350 separates
them well for the typical 1998-vintage Soviet-style chess book scans this
skill targets. Adjust if needed:
- If a real piece shows as "." (empty): lower the threshold or check the crop
- If empty squares show as "#" (false positive): raise the threshold

OUTPUT:
    Two grids printed to stdout:
    1. Raw ink density per square (rank 8 at top, rank 1 at bottom)
    2. Occupancy map: # for piece, . for empty, threshold-based

Use this BEFORE finalizing any FEN. It catches "is the king on g6 or f6?"
errors that destroy your work otherwise.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def find_borders(arr):
    """Locate the four border lines of the board.

    Returns (top, bottom, left, right) pixel coordinates, or None if the
    board cannot be located. Works by finding rows/columns where most
    pixels are very dark (< 80 / 255), which corresponds to the thick
    black border lines drawn around chess diagrams.
    """
    H, W = arr.shape

    # Horizontal borders: rows where >60% of pixels are dark
    row_dark = (arr < 80).sum(axis=1)
    top_candidates = np.where(row_dark > 0.6 * W)[0]
    if len(top_candidates) == 0:
        return None
    top = int(top_candidates[0])
    bottom = int(top_candidates[-1])

    # Vertical borders: columns where >70% of pixels (within the horizontal
    # band) are dark. Threshold is higher because the inner board has more
    # contrast than the page edges.
    band = arr[top + 5:bottom - 5, :]
    if band.shape[0] == 0:
        return None
    col_dark = (band < 80).sum(axis=0)
    col_candidates = np.where(col_dark > 0.7 * (bottom - top))[0]
    if len(col_candidates) == 0:
        return None
    left = int(col_candidates[0])
    right = int(col_candidates[-1])

    return top, bottom, left, right


def measure_squares(image_path, threshold=60, inner=0.6, borders=None):
    """For a board image, compute ink density per square.

    Args:
        image_path: path to JPG/PNG of a chess diagram crop.
        threshold: pixel value below which a pixel counts as "ink".
        inner: fraction of the square's center to sample. Smaller means
            more conservative (avoids border bleed and shading edge), but
            risks missing pieces drawn near a corner. 0.6 is a good default.
        borders: optional manual override (top, bottom, left, right).

    Returns:
        (8x8 numpy array of ink counts, (top, bottom, left, right)).
        The grid is indexed grid[rank_idx][file_idx] where rank_idx=0 is
        rank 8 (top of board) and file_idx=0 is the a-file.
    """
    img = Image.open(image_path).convert("L")
    arr = np.array(img)

    if borders is None:
        borders = find_borders(arr)
        if borders is None:
            raise RuntimeError(
                f"Could not auto-locate board borders in {image_path}. "
                "Re-crop tighter, or pass --borders explicitly."
            )

    top, bottom, left, right = borders
    sq_h = (bottom - top) / 8
    sq_w = (right - left) / 8

    grid = np.zeros((8, 8), dtype=int)
    inner_offset = (1 - inner) / 2
    inner_extent = (1 + inner) / 2

    for ri in range(8):  # 0 = rank 8 (top)
        r1 = int(top + ri * sq_h + sq_h * inner_offset)
        r2 = int(top + ri * sq_h + sq_h * inner_extent)
        for fi in range(8):  # 0 = file a (left)
            c1 = int(left + fi * sq_w + sq_w * inner_offset)
            c2 = int(left + fi * sq_w + sq_w * inner_extent)
            sub = arr[r1:r2, c1:c2]
            grid[ri, fi] = (sub < threshold).sum()

    return grid, borders


def print_grids(grid, occupied_threshold=350):
    """Pretty-print the ink density grid and a thresholded occupancy map."""
    print("Ink density per square (inner sample):")
    print("    a    b    c    d    e    f    g    h")
    for ri in range(8):
        rank = 8 - ri
        cells = " ".join(f"{grid[ri, fi]:4d}" for fi in range(8))
        print(f"{rank}: {cells}")

    print()
    print(f"Occupancy (# = piece, ink > {occupied_threshold}):")
    print("    a b c d e f g h")
    for ri in range(8):
        rank = 8 - ri
        cells = " ".join("#" if grid[ri, fi] > occupied_threshold else "."
                         for fi in range(8))
        print(f"{rank}:  {cells}")


def main():
    parser = argparse.ArgumentParser(
        description="Measure ink density on a chess diagram crop.",
        epilog="Squares with ink > threshold (default 350) are reported as "
               "occupied. Adjust if your scan differs from the typical case.",
    )
    parser.add_argument("image", type=Path, help="Path to the diagram crop.")
    parser.add_argument(
        "--threshold", type=int, default=350,
        help="Ink count above which a square is reported as occupied.",
    )
    parser.add_argument(
        "--inner", type=float, default=0.6,
        help="Fraction of square center to sample (0.0-1.0).",
    )
    parser.add_argument(
        "--pixel-threshold", type=int, default=60,
        help="Pixel value below which a pixel is counted as ink.",
    )
    parser.add_argument(
        "--borders", type=int, nargs=4, metavar=("TOP", "BOTTOM", "LEFT", "RIGHT"),
        help="Manual border override if auto-detection fails.",
    )
    args = parser.parse_args()

    if not args.image.exists():
        print(f"Error: {args.image} does not exist", file=sys.stderr)
        sys.exit(1)

    try:
        grid, borders = measure_squares(
            args.image,
            threshold=args.pixel_threshold,
            inner=args.inner,
            borders=tuple(args.borders) if args.borders else None,
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    print(f"Borders: top={borders[0]}, bottom={borders[1]}, "
          f"left={borders[2]}, right={borders[3]}")
    print_grids(grid, occupied_threshold=args.threshold)


if __name__ == "__main__":
    main()
