---
name: chess-puzzles-to-pgn
description: Transcribe chess puzzles from a scanned PDF book into a multi-chapter PGN file ready for Lichess study import. Each diagram becomes one chapter with its FEN, side-to-move, and a comment. Use this whenever a user asks to "convert a chess puzzle book to PGN", "make a Lichess study from this book", "transcribe diagrams to FEN", "import puzzles into Lichess", or hands you a PDF (especially a scanned/grayscale one) of chess problems and wants the positions in a digital format. Also use when working with Russian or other non-English chess books — the skill covers piece-letter translations and notation conventions. Don't try to do this work by eyeballing diagrams alone; the measurement workflow in this skill is what makes the output reliably accurate.
---

# Chess puzzles to PGN

Transcribe chess diagrams from a scanned book PDF into a Lichess-compatible PGN. The default deliverable is a verified PGN ready to import into Lichess with no user cleanup. If the chapter count would exceed what comfortably fits in one Lichess study, split it into multiple PGNs automatically.

## Why this skill exists

Eyeballing piece positions on a 1998-era grayscale scan does not work. Pieces near a file boundary (e.g. is the rook on g4 or h4?) are systematically misread, and a single wrong square breaks the whole puzzle. This skill enforces a workflow that catches those errors before the file ships.

The single most important rule: **never finalize a FEN you only looked at. Measure it.**

The second most important rule: **do not hand the user a first draft.** The user should be able to hand over a PDF and receive PGN output without doing your QA for you.

The third most important rule: **raw OCR / model / engine output is never final data.** It may suggest a candidate FEN, but it cannot be shipped until it has been checked square-by-square against the source board image.

For clean multi-diagram pages, board numbering must come from deterministic full-page recrops in reading order, not from any pre-existing manual crop filenames or detector output order.

Important: **2x3 is not a universal assumption.** It is one supported layout mode for clean puzzle-book pages. Other books may use 1x2, 2x2, 3x3, mixed counts, composites, or irregular placements.

Supported safe modes now are:
- detector/discovery + explicit review mapping
- declared-grid deterministic recrops (for example `3x2`, `2x2`, `1x2`) when the page layout is regular and known

If the page has multiple diagrams and you do not know the layout, fail closed: do not trust automated numbering until the layout is declared or explicitly reviewed.

## Setup

This skill uses Python plus two packages for image analysis: `numpy` and `Pillow`.

Recommended setup:

```bash
cd skills/chess-puzzles-to-pgn
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

When running the image-analysis scripts directly, prefer the venv Python:

```bash
.venv/bin/python scripts/automate_book.py --pdf input.pdf --output-dir out/book
.venv/bin/python scripts/extract_boards.py pages/*.png --output-dir out/crops --manifest out/boards.json
.venv/bin/python scripts/detect_occupancy.py <crop.jpg>
.venv/bin/python scripts/check_fens.py <pgn-file>
.venv/bin/python scripts/build_pgn.py <output.pgn>
```

For rasterizing source PDFs, `pdftoppm` is recommended when available.

## Automation now included

The skill now automates the front half of the workflow:
- PDF rasterization
- page-by-page board candidate discovery
- crop export
- JSON manifest generation for review

What is still manual on purpose:
- piece identity
- piece color
- side-to-move confirmation
- final FEN authorship
- final verification against the source before delivery

What must never happen again:
- treating detector order as chapter order without explicit reading-order mapping
- treating one page-layout assumption (like 2x3) as universal when the source format differs
- auto-numbering a multi-diagram page without either a declared grid or explicit review mapping
- treating model output as authoritative without source-image audit
- sending an engine-rebuilt PGN before square-by-square verification is complete

## Workflow

### 1. Survey the source

Read the PDF first to understand its scope. Use the `pdf-reading` skill if it's available, otherwise `pdftoppm` to rasterize the relevant pages at 250 DPI:

```bash
mkdir -p hires
pdftoppm -jpeg -r 250 input.pdf hires/p
```

Lower DPI loses detail in the small piece glyphs. Higher than 300 DPI is wasted; the source scan rarely has that much real resolution.

Walk through the rasterized pages and catalog:
- Diagram numbers (e.g., D224–D276)
- Puzzle numbers (often separate from diagram numbers — a puzzle "141" might use "diagram 229")
- Side-to-move ("Ход белых" = White to move, "Ход чёрных" = Black to move in Russian books)
- The mate-in-N or task description for each
- **Composite diagrams**: a single board image showing 2 or 4 sub-positions divided by inner borders (e.g., the D236 composite shows four queen-mate models labelled I, II, III, IV). These are common in pedagogical books and must be split into separate chapters.

Make a list before transcribing. Don't transcribe as you go.

### 2. Crop each diagram

You can now automate the initial crop-discovery step:

For regular clean pages with a known layout, prefer declared-grid recrops so numbering is deterministic:

```bash
python scripts/automate_book.py --pages-dir pages --output-dir out/book \
  --grid-page "page-2.png:3x2:1-7,1-10,1-8,1-11,1-9,1-12"
```

Or directly:

```bash
python scripts/recrop_page_grid.py --page page-2.png --grid 3x2 \
  --labels 1-7,1-10,1-8,1-11,1-9,1-12 --out-dir out/page-2
```

If the page layout is not known, do **not** guess a grid. Use detection plus explicit review instead.

You can also automate the initial crop-discovery step:

```bash
python scripts/automate_book.py --pdf input.pdf --output-dir out/book --annotate
```

That creates:
- `out/book/pages/` — rasterized page images
- `out/book/crops/` — likely board crops
- `out/book/manifest.json` — per-crop review manifest
- `out/book/summary.json` — page/candidate counts

Or, if you already have page images:

```bash
python scripts/extract_boards.py pages/*.png --output-dir out/crops --manifest out/boards.json --annotate
```

Then review the candidate crops and keep the ones that actually correspond to diagrams.

For each confirmed diagram, crop a region of the page raster that includes:
- The full board
- **Rank labels (1–8) on the left**
- **File labels (a–h) on the bottom**

The labels are non-negotiable — they're the only ground truth for which file/rank a piece is on. A crop without labels forces you to guess, and guessing is what produces wrong FENs.

Save crops to a `verify/` directory with names like `d224.jpg`, `d236.jpg`, etc.

### 3. Transcribe + measure

For each crop, do **both** steps:

**(a) Visual pass.** List every piece you see, with its color, type, and square. Russian books use Cyrillic piece letters in text (not on the board): Кр=K, Ф=Q, Л=R, С=B, К=N, п=pawn. The board glyphs themselves are standard.

**(b) Measurement pass.** Run `scripts/detect_occupancy.py <crop>` to get an 8×8 grid of ink density per square. Squares with a piece show much higher ink than empty squares. Compare the grid to your visual transcription. Discrepancies are usually you misreading a file or rank by one — the measurement is almost always right.

Use measurement especially for:
- Pieces on adjacent files (e.g., is the king on f6 or g6?)
- Pieces near the board edge
- Crowded clusters where pieces touch
- Anything you're not 100% certain about

If measurement and your eyes disagree, re-examine the crop carefully. Trust the measurement unless you can clearly see why it's wrong (occasional false positives from very dark shading texture).

See `references/measurement.md` for how the tool works and how to interpret its output.

### 4. Encode the FEN

For each diagram, build the FEN:
- Position field: rank 8 first, ending with rank 1, files separated by `/`
- White pieces uppercase (`KQRBNP`), black lowercase (`kqrbnp`)
- Empty square runs as digits 1–8
- Side-to-move: `w` or `b` based on the book's prompt
- Castling: `-` (puzzle positions don't have castling rights)
- En passant: `-`
- Halfmove/fullmove: `0 1`

Example: `7k/4R3/6K1/8/8/8/8/8 w - - 0 1`

### 5. Validate every FEN

Run `scripts/check_fens.py <pgn-file>` (or call the validation function on each FEN before writing). It catches:
- Wrong number of ranks
- Ranks that don't sum to 8
- Missing or duplicate kings
- **Kings on adjacent squares** (illegal, and a common transcription error)
- Bad side-to-move character

Validation does not prove the FEN matches the diagram — it only proves the FEN is structurally legal. Visual + measurement is what proves correctness.

### 6. Build the PGN

Final delivery PGNs should be clean. Do not inject internal workflow notes such as audit provenance, crop-order fixes, or numbering/debug comments into the chapter body unless the user explicitly asked for them.

Use `scripts/build_pgn.py` as a template. Each chapter needs:

```
[Event "01. Lesson · D224a — Two-rook mate pattern (corner)"]
[Site "Book title and page range"]
[Date "YYYY.??.??"]
[Round "1"]
[White "224a White to move"]
[Black "?"]
[Result "*"]
[SetUp "1"]
[FEN "2k4R/6R1/8/4K3/8/8/8/8 b - - 0 1"]
[Annotator "Source"]

{ Comment describing the puzzle and side to move. } *
```

**Lichess-specific quirks** (these are what burned me the first time and you should not relearn them):

1. The chapter label in the Lichess sidebar comes from `[White]`, not `[Event]`. Put the diagram number and side-to-move in `[White]` so the sidebar shows e.g. `225 White to move` instead of just `White to move`. The `[Event]` field is still useful as the canonical title in the chapter detail view, so put the full descriptive title there.

2. Prefix `[Event]` titles with a 2-digit sequence number (`01.`, `02.`, … `60.`) so chapters stay in book order regardless of how Lichess sorts them.

3. `[SetUp "1"]` and `[FEN ...]` together tell Lichess this is a puzzle position, not a regular game. Both are required.

4. End the body with `*` (game in progress / no result), since these are puzzles, not finished games. If there is no user-facing annotation to include, use a bare `*` with no comment block.

5. Composite diagrams: split into multiple chapters with sub-IDs like `224a`, `224b`, `236-I`, `236-II`, `236-III`, `236-IV`, `258-I` etc. When extracting these into the `[White]` sidebar label, watch the regex: try `IV` before `I`, `II`, `III`, otherwise `236-IV` becomes `236-I` (this bit me).

### 7. Mandatory verification pass

Before delivery, do a full verification pass over every chapter.

For clear PDFs, generate labeled audit sheets first. Every board should have:
- a stable source crop in reading order
- a labeled square contact sheet (`a8` through `h1`)
- a final audit where each occupied square in the FEN is checked against that sheet

Minimum standard:
1. Re-open the original board crop or page crop for each position.
2. Re-check every occupied square against the FEN, not just the ones that felt uncertain the first time.
3. Re-check side to move against the printed prompt.
4. Re-run `scripts/check_fens.py` on the final PGN after all corrections.
5. If the source spans multiple pages, verify the assembled combined PGN, not just per-page fragments.

Preferred workflow:
- First pass: transcription + measurement.
- Second pass: independent visual audit against the source image.
- Final pass: structural validation of the exact delivered PGN file.

Do not send a "first-pass" PGN unless the user explicitly asked for an unfinished draft.
Do not ask the user to spot-check your work unless you are genuinely blocked by an unreadable diagram.

### 8. Deliver

Save the final PGN to the outputs directory. If the chat/channel supports file delivery, send the actual PGN file(s) to the user as attachments; do **not** stop at reporting machine-local paths. Only fall back to plain path reporting when attachment delivery is unavailable.

Tell the user how to import it: in Lichess, create a study, then "New chapter" → "PGN" tab → paste the file (or upload).

If the total chapter count is large enough to be awkward for a single Lichess study, split automatically into multiple PGNs and label the ranges clearly (for example `001-064`, `065-128`, etc.).

Mention any caveats: the Lichess study creates many chapters from one paste; the user should import as a study, not as a single game.

## Common failure modes

Don't repeat these. They all happened on the first attempt that produced this skill.

**Misreading a piece by one file.** Pieces near file boundaries (especially g/h, a/b) get assigned the wrong file when eyeballed. Always run measurement on these.

**Black rook vs. white rook.** Filled glyph = black, hollow/outline = white. On a noisy scan with shading texture, a hollow rook on a dark square can look filled. If the resulting FEN gives an impossible position (e.g., side-to-move is in check from no clear source), recheck rook colors.

**Kings adjacent.** Always illegal, always a transcription error. The validator catches this; don't ship a FEN that fails the validator.

**Composite boards transcribed as one position.** If a board has internal black lines splitting it into quadrants, those are separate diagrams. Look for Roman numerals (I, II, III, IV) or letters (a, b) in the source labelling.

**Confusing puzzle numbers and diagram numbers.** Russian books often have separate sequences: "Puzzle 141 (see diagram 229)". Use diagram numbers as the canonical reference (they're unique within the book and continuous across lesson/puzzle sections); puzzle numbers can collide and skip.

**Wrong side-to-move.** The Russian phrase right before the diagram tells you: "Ход белых" = White, "Ход чёрных" = Black. For lesson positions illustrating a technique, the side that demonstrates the technique is usually to move; for already-mated reference positions, it doesn't matter, but conventionally use the side that just lost.

**Forgetting to crop with labels.** A crop without rank/file labels at the edges is useless for verification. Re-crop with more margin.

**Stopping after structural validation.** A FEN can be legal and still be wrong. `check_fens.py` catches impossible structures, not transcription mistakes. Always do the separate source-image verification pass.

## Files in this skill

- `scripts/automate_book.py` — orchestration entry point: rasterize PDF, find board candidates, export crops, write manifest.
- `scripts/extract_boards.py` — scan page images for likely board regions and crop them.
- `scripts/recrop_page_grid.py` — deterministically recrop clean 2x3 puzzle pages in reading order so numbering cannot drift.
- `scripts/detect_occupancy.py` — measures ink density per board square, prints an 8×8 grid. The single most important verification tool here.
- `scripts/check_fens.py` — structural FEN validator (kings, ranks, side-to-move).
- `scripts/build_pgn.py` — template for assembling the multi-chapter PGN. Adapt the `chapters` list to your book.
- `references/measurement.md` — how `detect_occupancy.py` works, calibration notes, threshold tuning.
- `references/russian_chess_notation.md` — Cyrillic piece letters, common phrases, glossary.
- `references/lichess_pgn_format.md` — the exact PGN headers Lichess wants and why.

## Default behavior expectations

When the user gives you a puzzle PDF and asks for PGN / a Lichess study import file:
- do the full extraction workflow yourself
- verify before sending
- split into multiple PGNs automatically if needed for study size
- avoid asking the user process questions unless the source is genuinely unreadable or corrupted
- deliver the finished PGN file(s) to the user when the channel supports attachments, not just local path(s)
- return the finished file path(s) too when useful, but never instead of the actual file if attachment delivery is available
