---
name: openings-coach
description: Analyze chess games against Aman Hambleton-style Stonewall and French reference corpora. Use when a user wants opening-specific feedback, Stonewall or French pattern analysis, or help maintaining the related cheat-sheet workflows. Not for general chess questions unrelated to those openings.
---

# Openings Coach

Use this skill for **Stonewall** and **French Defense** analysis built around a local reference corpus.

It is most useful when you have already built a PGN database containing example games from the opening family you care about.

## Main uses

- analyze a submitted game through a Stonewall or French lens
- answer opening-specific pattern questions
- maintain Stonewall or French cheat-sheet generation workflows

## Step 1: Detect the opening first

Before giving opening-specific advice, identify which bucket the game actually belongs to.

Use `chess_tools/parse_pgn.py` or another proper PGN parser. Do **not** use one-line regex parsing.

### Stonewall cues
- White Stonewall: `d4`, `e3`, `f4`, and usually `Bd3`
- Black Stonewall: `d5`, `e6`, `f5`, and typically `Bd6`

### French cues
- `1. e4 e6` as Black
- then classify the variation from the moves, not from ECO labels alone

If the game is neither Stonewall nor French, give general chess feedback instead of forcing it into the framework.

## Mode 1: Game analysis

### Stonewall questions to answer

For White:
- Was the move order coherent?
- Was `Bd3` prioritized sensibly?
- Was `Ne5` established or prepared at the right time?
- Was `Nd2` used to support the center when needed?
- Did the game justify a `g4` storm, `e4` break, or bishop sacrifice idea?

For Black:
- Was the wall built cleanly before drifting into side plans?
- Did `Ne4` become the central plan?
- Was the bad bishop improved, exchanged, or left trapped?
- Was the kingside expansion timed correctly?
- Was the position handled patiently rather than tactically forcing matters too early?

### French questions to answer

- Which variation appeared: Exchange, Advanced, Winawer, Tarrasch, Classical, or sideline?
- Was the light-squared bishop problem handled well?
- Was the correct plan chosen for the actual variation on the board?
- In Advanced lines, was the pawn chain attacked at the base?
- In Exchange lines, was the plan selection sensible?
- In Winawer lines, were the standard structural ideas understood?
- Was the castling choice consistent with the pawn structure and middlegame plan?

### Report format

Use a short report card with opening-relevant criteria only.

Suggested structure:

| Principle | Grade | Notes |
|-----------|-------|-------|
| move order / plan | ✅ / 🟡 / ❌ | concrete move-based observation |
| key strategic theme | ✅ / 🟡 / ❌ | what was handled well or poorly |

End with:

**Single biggest improvement:** one practical takeaway tied to a specific moment in the game.

## Mode 2: Cheat-sheet maintenance

If you maintain local Stonewall or French cheat-sheet generators, this skill can also drive those workflows.

Relevant public scripts in this repo:
- `chess_tools/tag_games.py`
- `chess_tools/tag_french.py`
- `chess_tools/generate_pdf.py`
- `chess_tools/generate_french_pdf.py`

Typical workflow:
1. inspect the relevant tagging/generator scripts first
2. update the logic or prose
3. regenerate the output locally
4. verify the output before sharing it

Generated PDFs are local outputs; they are not the canonical document layer in this public repo.

## Mode 3: Pattern questions

Use this skill when someone asks opening-specific questions such as:
- how often a Stonewall plan appears
- how a French structure is typically handled
- what recurring ideas show up in an Aman-style corpus

For pattern questions:
1. query the local corpus with `chess_tools/parse_pgn.py` or the search stack
2. compute counts from current data instead of quoting stale numbers
3. link example games when possible

## Key files

| File | Purpose |
|------|---------|
| `chess_tools/parse_pgn.py` | PGN parser |
| `chess_tools/tag_games.py` | Stonewall tagging helpers |
| `chess_tools/tag_french.py` | French tagging helpers |
| `chess_tools/generate_pdf.py` | Stonewall PDF generator |
| `chess_tools/generate_french_pdf.py` | French PDF generator |
| `skills/openings-coach/references/stonewall-notes.md` | Stonewall-specific notes and anti-regression context |

## Critical rules

- detect the opening before analyzing
- use a real PGN parser
- verify statistics from current data
- do not force Stonewall criteria onto French games or vice versa
- prefer concrete move-based feedback over vague stylistic claims
