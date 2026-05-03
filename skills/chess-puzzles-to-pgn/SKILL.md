---
name: chess-puzzles-to-pgn
description: Transcribe chess puzzles from a scanned PDF book into a multi-chapter PGN file ready for Lichess study import. Each diagram becomes one chapter with its FEN, side-to-move, and a comment. Use this whenever a user asks to "convert a chess puzzle book to PGN", "make a Lichess study from this book", "transcribe diagrams to FEN", "import puzzles into Lichess", or hands you a PDF (especially a scanned/grayscale one) of chess problems and wants the positions in a digital format. Also use when working with Russian or other non-English chess books — the skill covers piece-letter translations and notation conventions. Don't try to do this work by eyeballing diagrams alone; the measurement workflow in this skill is what makes the output reliably accurate.
---

# Chess puzzles to PGN

Transcribe chess diagrams from a scanned book PDF into a Lichess-compatible PGN. The output is one PGN file with each diagram as a chapter; the user pastes or uploads it into the Lichess study importer.

## Why this skill exists

Eyeballing piece positions on a 1998-era grayscale scan does not work. Pieces near a file boundary (e.g. is the rook on g4 or h4?) are systematically misread, and a single wrong square breaks the whole puzzle. This skill enforces a workflow that catches those errors before the file ships.

The single most important rule: **never finalize a FEN you only looked at. Measure it.**

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
.venv/bin/python scripts/detect_occupancy.py <crop.jpg>
.venv/bin/python scripts/check_fens.py <pgn-file>
.venv/bin/python scripts/build_pgn.py <output.pgn>
```

For rasterizing source PDFs, `pdftoppm` is recommended when available.

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

For each diagram, crop a region of the page raster that includes:
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

4. End the body with `*` (game in progress / no result), since these are puzzles, not finished games.

5. Composite diagrams: split into multiple chapters with sub-IDs like `224a`, `224b`, `236-I`, `236-II`, `236-III`, `236-IV`, `258-I` etc. When extracting these into the `[White]` sidebar label, watch the regex: try `IV` before `I`, `II`, `III`, otherwise `236-IV` becomes `236-I` (this bit me).

### 7. Deliver

Save the final PGN to the outputs directory. Tell the user how to import it: in Lichess, create a study, then "New chapter" → "PGN" tab → paste the file (or upload).

Mention any caveats: the Lichess study creates 60 chapters from one paste; the user should import as a study, not as a single game.

## Common failure modes

Don't repeat these. They all happened on the first attempt that produced this skill.

**Misreading a piece by one file.** Pieces near file boundaries (especially g/h, a/b) get assigned the wrong file when eyeballed. Always run measurement on these.

**Black rook vs. white rook.** Filled glyph = black, hollow/outline = white. On a noisy scan with shading texture, a hollow rook on a dark square can look filled. If the resulting FEN gives an impossible position (e.g., side-to-move is in check from no clear source), recheck rook colors.

**Kings adjacent.** Always illegal, always a transcription error. The validator catches this; don't ship a FEN that fails the validator.

**Composite boards transcribed as one position.** If a board has internal black lines splitting it into quadrants, those are separate diagrams. Look for Roman numerals (I, II, III, IV) or letters (a, b) in the source labelling.

**Confusing puzzle numbers and diagram numbers.** Russian books often have separate sequences: "Puzzle 141 (see diagram 229)". Use diagram numbers as the canonical reference (they're unique within the book and continuous across lesson/puzzle sections); puzzle numbers can collide and skip.

**Wrong side-to-move.** The Russian phrase right before the diagram tells you: "Ход белых" = White, "Ход чёрных" = Black. For lesson positions illustrating a technique, the side that demonstrates the technique is usually to move; for already-mated reference positions, it doesn't matter, but conventionally use the side that just lost.

**Forgetting to crop with labels.** A crop without rank/file labels at the edges is useless for verification. Re-crop with more margin.

## Files in this skill

- `scripts/detect_occupancy.py` — measures ink density per board square, prints an 8×8 grid. The single most important tool here.
- `scripts/check_fens.py` — structural FEN validator (kings, ranks, side-to-move).
- `scripts/build_pgn.py` — template for assembling the multi-chapter PGN. Adapt the `chapters` list to your book.
- `references/measurement.md` — how `detect_occupancy.py` works, calibration notes, threshold tuning.
- `references/russian_chess_notation.md` — Cyrillic piece letters, common phrases, glossary.
- `references/lichess_pgn_format.md` — the exact PGN headers Lichess wants and why.
