#!/usr/bin/env python3
"""
Automate the front half of the puzzle-book workflow:
- rasterize a PDF into page images (optional)
- either detect likely board regions OR deterministically recrop declared-grid pages
- crop them into a review directory
- build a JSON manifest for the remaining human verification steps

USAGE:
    python automate_book.py --pdf input.pdf --output-dir out/book
    python automate_book.py --pages-dir out/book/pages --output-dir out/book
    python automate_book.py --pages-dir out/book/pages --output-dir out/book \
        --grid-page "page-2.png:3x2:1-7,1-10,1-8,1-11,1-9,1-12"
"""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from extract_boards import crop_candidates, find_board_candidates
from recrop_page_grid import find_boxes


IMAGE_EXTS = {".png", ".jpg", ".jpeg"}


def rasterize_pdf(pdf_path, pages_dir, dpi=250, fmt="png"):
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm not found. Install poppler-utils or pass --pages-dir.")

    pages_dir.mkdir(parents=True, exist_ok=True)
    prefix = pages_dir / "page"
    cmd = [pdftoppm, f"-{fmt}", "-r", str(dpi), str(pdf_path), str(prefix)]
    subprocess.run(cmd, check=True)


def sorted_page_images(pages_dir):
    return sorted(
        p for p in pages_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def build_summary(manifest_rows):
    by_page = {}
    for row in manifest_rows:
        by_page.setdefault(row["source_page"], 0)
        by_page[row["source_page"]] += 1
    return {
        "page_count": len(by_page),
        "candidate_count": len(manifest_rows),
        "pages": [{"page": page, "candidates": count} for page, count in sorted(by_page.items())],
    }


def grid_recrop_page(page_image, grid_spec, labels, crops_dir):
    page_image = Path(page_image)
    if "x" not in grid_spec.lower():
        raise SystemExit(f"Grid page {page_image.name} needs ROWSxCOLS grid spec, got {grid_spec!r}")
    rows_s, cols_s = grid_spec.lower().split("x", 1)
    expected_rows = int(rows_s)
    expected_cols = int(cols_s)
    expected_count = expected_rows * expected_cols

    labels = [x.strip() for x in labels.split(",") if x.strip()]
    if len(labels) != expected_count:
        raise SystemExit(
            f"Grid page {page_image.name} needs exactly {expected_count} labels for grid {grid_spec}, got {len(labels)}"
        )

    boxes = find_boxes(page_image, expected_rows=expected_rows, expected_cols=expected_cols)
    img = Image.open(page_image).convert("RGB")
    rows = []
    for (x, y, w, h), label in zip(boxes, labels):
        left = max(0, x - 70)
        top = max(0, y - 30)
        right = min(img.width, x + w + 25)
        bottom = min(img.height, y + h + 80)
        crop = img.crop((left, top, right, bottom))
        out_path = crops_dir / f"{label}.png"
        crop.save(out_path)
        rows.append({
            "source_page": str(page_image),
            "crop_path": str(out_path),
            "candidate_index": len(rows) + 1,
            "board_bbox": {"top": y, "bottom": y + h - 1, "left": x, "right": x + w - 1},
            "crop_bbox": {"top": top, "bottom": bottom - 1, "left": left, "right": right - 1},
            "border_score": None,
            "inner_density": None,
            "status": "needs_review",
            "diagram_id": label,
            "side_to_move": "",
            "comment": "deterministic_grid_recrop",
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description="Rasterize a puzzle book and extract likely chess-board crops.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pdf", type=Path, help="Source puzzle-book PDF.")
    group.add_argument("--pages-dir", type=Path, help="Pre-rendered page-image directory.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Working directory for pages/crops/manifest.")
    parser.add_argument("--dpi", type=int, default=250, help="Rasterization DPI when using --pdf.")
    parser.add_argument("--format", choices=("png", "jpeg"), default="png", help="Page image format when rasterizing.")
    parser.add_argument("--min-size", type=int, default=110, help="Minimum candidate board size on the detection image.")
    parser.add_argument("--max-dim", type=int, default=1600, help="Downsample long edge to this many pixels for detection.")
    parser.add_argument("--annotate", action="store_true", help="Save page images with candidate boxes drawn.")
    parser.add_argument(
        "--grid-page",
        action="append",
        default=[],
        help="Deterministic grid recrop override: 'page-filename.png:ROWSxCOLS:label1,label2,...' in reading order.",
    )
    args = parser.parse_args()

    output_dir = args.output_dir
    pages_dir = args.pages_dir or (output_dir / "pages")
    crops_dir = output_dir / "crops"
    manifest_path = output_dir / "manifest.json"
    summary_path = output_dir / "summary.json"

    output_dir.mkdir(parents=True, exist_ok=True)
    crops_dir.mkdir(parents=True, exist_ok=True)

    if args.pdf:
        if not args.pdf.exists():
            raise SystemExit(f"Missing PDF: {args.pdf}")
        rasterize_pdf(args.pdf, pages_dir, dpi=args.dpi, fmt=args.format)

    if not pages_dir.exists():
        raise SystemExit(f"Pages directory does not exist: {pages_dir}")

    page_images = sorted_page_images(pages_dir)
    if not page_images:
        raise SystemExit(f"No page images found in {pages_dir}")

    grid_map = {}
    for item in args.grid_page:
        parts = item.split(":", 2)
        if len(parts) != 3:
            raise SystemExit(f"Bad --grid-page entry: {item!r}")
        name, grid_spec, labels = parts
        grid_map[name.strip()] = (grid_spec.strip(), labels.strip())

    all_rows = []
    for page_image in page_images:
        if page_image.name in grid_map:
            grid_spec, labels = grid_map[page_image.name]
            rows = grid_recrop_page(page_image, grid_spec, labels, crops_dir)
            all_rows.extend(rows)
            print(f"{page_image.name}: {len(rows)} deterministic grid crop(s)")
            continue

        candidates = find_board_candidates(page_image, min_size=args.min_size, max_dim=args.max_dim)
        rows, annotated = crop_candidates(page_image, candidates, crops_dir, annotate=args.annotate)
        all_rows.extend(rows)
        print(f"{page_image.name}: {len(rows)} candidate board(s)")
        if annotated:
            print(f"  annotated: {annotated}")

    manifest_path.write_text(json.dumps(all_rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary_path.write_text(json.dumps(build_summary(all_rows), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nManifest -> {manifest_path}")
    print(f"Summary  -> {summary_path}")
    print(f"Crops    -> {crops_dir}")
    print("\nNext step: review the crops, fill in diagram ids / side to move, then transcribe and validate FENs.")


if __name__ == "__main__":
    main()
