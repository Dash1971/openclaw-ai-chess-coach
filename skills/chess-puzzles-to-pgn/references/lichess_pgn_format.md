# Lichess study PGN format

What Lichess actually does with each PGN header, and the quirks that bite
you if you don't know them.

## Importing a multi-chapter study

Lichess studies accept a single PGN file containing multiple games separated
by blank lines. Each game becomes a chapter. To import:

1. Create or open a study on lichess.org/study.
2. Click the `+` (new chapter) button.
3. Choose the **PGN** tab.
4. Paste the entire multi-game PGN, or upload the file.
5. Click "Create chapters". All chapters are created at once.

There's also a single-position importer at lichess.org/paste, but for a
puzzle book you want the study importer — it preserves chapter structure
and lets the user navigate puzzle-to-puzzle.

## Required headers for a puzzle position

A chapter that starts from a custom position (i.e., not from the standard
starting position) needs **both** of these headers:

```
[SetUp "1"]
[FEN "k7/Pp6/1p6/1p3B2/1p3K2/1p6/8/R7 w - - 0 1"]
```

Without `[SetUp "1"]`, Lichess sometimes treats the FEN as advisory and
falls back to the standard starting position. With both, the chapter
loads exactly the FEN you specified.

## How each header is used

| Header       | Used by Lichess for             |
|--------------|---------------------------------|
| `[Event]`    | Chapter title in the chapter detail view (large header at the top of the analysis board). Not shown in the sidebar. |
| `[Site]`     | Generally ignored in study UI; useful as metadata. |
| `[Date]`     | Generally ignored in study UI. |
| `[Round]`    | Generally ignored in study UI. |
| `[White]`    | **The chapter label in the sidebar.** This is the gotcha. |
| `[Black]`    | Shown in the chapter info panel. |
| `[Result]`   | Shown in the chapter info panel. Use `*` for puzzles (game in progress). |
| `[SetUp]`    | Required to be `"1"` for custom positions. |
| `[FEN]`      | The starting position. |
| `[Annotator]`| Shown in the chapter info panel. |

## The `[White]` sidebar quirk

This is the single most surprising thing about Lichess studies. The sidebar
chapter list uses the `[White]` header as the label, **not** `[Event]`.

If your `[White]` is just `"White to move"`, the sidebar shows a long
identical list:

```
1   White to move
2   White to move
3   White to move
...
```

This is useless for navigation. Instead, put the diagram identifier and
side-to-move in `[White]`:

```
[White "229 White to move"]
```

Now the sidebar shows:

```
1   224a Reference position
2   224b Reference position
3   225 White to move
4   226 White to move
...
```

The full descriptive title (e.g., `"03. Lesson · D225 — Ladder/linear
mate (worked example)"`) goes in `[Event]` and is visible above the board
when you click into the chapter.

## Chapter ordering

Lichess sorts chapters in the study by a combination of insertion order
and the chapter title. To guarantee they stay in book order regardless of
import behavior, prefix the `[Event]` title with a 2-digit sequence number:

```
[Event "01. Lesson · D224a — Two-rook mate pattern (corner)"]
[Event "02. Lesson · D224b — Two-rook mate pattern (centre)"]
[Event "03. Lesson · D225 — Ladder/linear mate (worked example)"]
```

This isn't strictly necessary if your import order is preserved, but it's
cheap insurance.

## Composite diagrams

Pedagogical books often combine 2 or 4 sub-positions into one printed
diagram (separated by inner black lines). Each sub-position becomes a
separate Lichess chapter. Use sub-IDs:

- Two halves: `224a`, `224b`
- Four quadrants: `236-I`, `236-II`, `236-III`, `236-IV`
  (Roman numerals match the book's labelling — typically I top-left,
   II top-right, III bottom-left, IV bottom-right)

When extracting these into the `[White]` sidebar label, the regex order
matters. `re.search(r'D(\d+)-(I{1,3}|IV)', title)` will match the leading
`I` of `IV` and grab `D236-I` instead of `D236-IV`. Either:

- Put longer alternatives first: `r'D(\d+)-(IV|III|II|I)\b'`, or
- Use `re.fullmatch`-style anchoring with `\b` to require the suffix to
  end at a word boundary.

## Comments

PGN comments go in `{ ... }` and appear in Lichess as text annotations
below the board. Keep them short — a one-line task description plus any
hints. The user reads the book for full context; the PGN comment just
needs to remind them which puzzle this is.

## Result field

For puzzles, always use `[Result "*"]` and end the body with `*`:

```
[Result "*"]
...
{ White to move. Mate in 2. } *
```

`1-0`, `0-1`, `1/2-1/2` would imply the game has finished, which is
wrong for a puzzle starting position. Lichess displays `*` as "ongoing"
which is correct for puzzles waiting to be solved.

## What NOT to do

- Don't include moves in the PGN body. The user is meant to solve the
  puzzle by playing moves on the board; pre-filling the answer ruins it.
  If you want to include the solution, put it in the comment as text:
  `{ Solution: 1.Qh7+ Kxh7 2.Rh1#. }`
- Don't use `[Variant]` headers unless the position is a variant
  (Chess960, etc.). Standard chess puzzles need no `[Variant]`.
- Don't put non-ASCII characters in `[White]` if you can avoid it. Some
  Lichess sidebar truncation breaks on Cyrillic. The `[Event]` and
  comment fields are fine for any UTF-8.
