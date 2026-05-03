#!/usr/bin/env python3
"""
Build a multi-chapter PGN ready for Lichess study import.

This is a TEMPLATE. Adapt the `chapters` list below to match the diagrams
in the book you're transcribing.

Each chapter needs:
- title: descriptive string used as [Event] header.
- fen: full FEN with all 6 fields.
- side_human: "White to move" / "Black to move" / "Reference position" /
              "(Stalemate)" — what shows in the Lichess sidebar after the
              diagram identifier.
- comment: prose annotation shown in the chapter body.

The output PGN can be pasted into Lichess: Study -> New chapter -> PGN tab.
Each [Event] becomes a chapter; [White] becomes the sidebar label.

USAGE:
    python build_pgn.py [output.pgn]
"""

import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Adapt this list for your book.
# ---------------------------------------------------------------------------
chapters = [
    # Example entries — replace with the diagrams from your source.
    ("Lesson · D224a — Two-rook mate pattern (corner)",
     "2k4R/6R1/8/4K3/8/8/8/8 b - - 0 1",
     "Reference position",
     "Reference: typical two-rook mate, king on the edge. Top half of D224 isolated. Black is already mated."),

    ("Lesson · D225 — Ladder/linear mate (worked example)",
     "8/8/8/8/5k2/8/6R1/4K2R w - - 0 1",
     "White to move",
     "Worked example showing the ladder/linear mate with two rooks (one cuts off, the other gives check)."),

    ("Puzzle 141 · D229 — Mate in 2",
     "3k4/8/8/8/8/8/2R5/KR6 w - - 0 1",
     "White to move",
     "White to move. Mate in 2."),
]

# ---------------------------------------------------------------------------
# Book metadata (set these once for your book).
# ---------------------------------------------------------------------------
SITE = "Source book title and page range"
DATE = "????.??.??"
ANNOTATOR = "Source"

# ---------------------------------------------------------------------------
# Helpers — usually don't need to touch these.
# ---------------------------------------------------------------------------

def short_id_from_title(title):
    """Extract the diagram identifier ('224a', '236-IV', '229') from a title.

    Try Roman-numeral-suffixed forms (D236-IV) before plain digit forms
    (D229) so that 236-IV doesn't get matched as just '236' or '236-I'.
    """
    # Composite with Roman suffix. Try IV before II/III/I (longer first!) so
    # 'D236-IV' doesn't match as 'D236-I' with -V left over.
    m = re.search(r"D(\d+)-(IV|III|II|I)\b", title)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    # Sub-letter suffix: D224a, D224b
    m = re.search(r"D(\d+)([a-z])\b", title)
    if m:
        return f"{m.group(1)}{m.group(2)}"
    # Plain diagram number
    m = re.search(r"D(\d+)", title)
    if m:
        return m.group(1)
    return ""


def make_chapter(idx, title, fen, side_human, comment):
    """Render one chapter as a PGN-formatted string.

    Lichess uses the [White] header as the sidebar label, so we put a short
    "{diagram_id} {side}" string there. The full descriptive title goes in
    [Event], prefixed with a 2-digit sequence number so chapters stay in
    book order regardless of how Lichess sorts them.
    """
    full_title = f"{idx:02d}. {title}"
    diagram_id = short_id_from_title(title)
    sidebar = f"{diagram_id} {side_human}" if diagram_id else side_human

    headers = [
        f'[Event "{full_title}"]',
        f'[Site "{SITE}"]',
        f'[Date "{DATE}"]',
        f'[Round "{idx}"]',
        f'[White "{sidebar}"]',
        f'[Black "?"]',
        f'[Result "*"]',
        f'[SetUp "1"]',
        f'[FEN "{fen}"]',
        f'[Annotator "{ANNOTATOR}"]',
    ]
    body = "{ " + comment + " } *"
    return "\n".join(headers) + "\n\n" + body + "\n"


def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("positions.pgn")
    pgn = "\n\n".join(make_chapter(i + 1, *c) for i, c in enumerate(chapters))
    out_path.write_text(pgn, encoding="utf-8")
    print(f"Wrote {len(chapters)} chapters -> {out_path}")


if __name__ == "__main__":
    main()
