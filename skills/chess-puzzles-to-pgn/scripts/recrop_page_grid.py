#!/usr/bin/env python3
"""
Deterministically crop a clean puzzle page into numbered board images using a
user-declared grid shape.

This is for pages where board order must come from page layout, not from
candidate/discovery order.

Usage:
  python recrop_page_grid.py --page page-2.png --grid 3x2 \
    --labels 1-7,1-10,1-8,1-11,1-9,1-12 --out-dir out/page-2

Grid semantics:
- --grid is ROWSxCOLS in reading order.
- labels must be supplied in reading order for that grid.
- the script finds board-like squares, clusters them into the declared row/column
  layout, pads each crop to include coordinate labels, and writes numbered crops.
"""

import argparse
from pathlib import Path

import cv2
from PIL import Image
import numpy as np


def find_boxes(page_path: Path, expected_rows: int = 3, expected_cols: int = 2):
    img = cv2.imread(str(page_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise SystemExit(f"Could not read page: {page_path}")
    _, th = cv2.threshold(img, 180, 255, cv2.THRESH_BINARY_INV)
    th = cv2.dilate(th, np.ones((3, 3), np.uint8), iterations=1)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = img.shape
    boxes = []
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        area = bw * bh
        if bw < 300 or bh < 300:
            continue
        aspect = bw / bh
        if not (0.75 < aspect < 1.25):
            continue
        if area >= 0.3 * w * h:
            continue
        boxes.append((x, y, bw, bh))
    expected_count = expected_rows * expected_cols
    if len(boxes) != expected_count:
        raise SystemExit(f"Expected {expected_count} board boxes, found {len(boxes)} on {page_path}")

    # Robust reading order: cluster into declared rows by y-center, then sort left-to-right within each row.
    centers = sorted(((y + bh / 2), i) for i, (x, y, bw, bh) in enumerate(boxes))
    rows = []
    row_threshold = 80
    for cy, idx in centers:
        placed = False
        for row in rows:
            if abs(cy - row['avg']) <= row_threshold:
                row['items'].append((cy, idx))
                row['avg'] = sum(v for v, _ in row['items']) / len(row['items'])
                placed = True
                break
        if not placed:
            rows.append({'avg': cy, 'items': [(cy, idx)]})
    rows.sort(key=lambda r: r['avg'])
    if len(rows) != expected_rows or any(len(r['items']) != expected_cols for r in rows):
        raise SystemExit(
            f"Could not form {expected_rows} rows of {expected_cols} boards on {page_path}: {rows}"
        )
    ordered = []
    for row in rows:
        row_boxes = [boxes[idx] for _, idx in row['items']]
        row_boxes.sort(key=lambda b: b[0])
        ordered.extend(row_boxes)
    return ordered


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", type=Path, required=True)
    ap.add_argument("--grid", required=True, help="Declared layout as ROWSxCOLS, e.g. 3x2 or 2x2")
    ap.add_argument("--labels", required=True, help="Comma-separated labels in reading order")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--pad-left", type=int, default=70)
    ap.add_argument("--pad-top", type=int, default=30)
    ap.add_argument("--pad-right", type=int, default=25)
    ap.add_argument("--pad-bottom", type=int, default=80)
    args = ap.parse_args()

    if "x" not in args.grid.lower():
        raise SystemExit("--grid must look like ROWSxCOLS, e.g. 3x2")
    rows_s, cols_s = args.grid.lower().split("x", 1)
    expected_rows = int(rows_s)
    expected_cols = int(cols_s)
    expected_count = expected_rows * expected_cols

    labels = [x.strip() for x in args.labels.split(",") if x.strip()]
    if len(labels) != expected_count:
        raise SystemExit(f"--labels must contain exactly {expected_count} labels for grid {args.grid}")

    boxes = find_boxes(args.page, expected_rows=expected_rows, expected_cols=expected_cols)
    page = Image.open(args.page).convert("RGB")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for (x, y, w, h), label in zip(boxes, labels):
        l = max(0, x - args.pad_left)
        t = max(0, y - args.pad_top)
        r = min(page.width, x + w + args.pad_right)
        b = min(page.height, y + h + args.pad_bottom)
        crop = page.crop((l, t, r, b))
        crop.save(args.out_dir / f"{label}.png")
        print(f"{label}: {x},{y},{w},{h} -> {args.out_dir / (label + '.png')}")


if __name__ == "__main__":
    main()
