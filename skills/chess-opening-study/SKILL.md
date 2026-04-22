---
name: chess-opening-study
description: Extract instructive French Defense or Stonewall games from a public chess.com account and turn them into a study-ready PGN. Use when a user wants an opening-specific study set rather than a general scouting report.
---

# Chess Opening Study Builder

Use this skill to build a **study-ready PGN** from a public chess.com account for either:
- **French Defense**
- **Stonewall**

This is different from general opponent scouting. Use it when the goal is to collect and annotate instructive games for later study import.

## Trigger conditions

All of these should be true:
1. there is a chess.com player link or username
2. there is an explicit opening keyword such as `French` or `Stonewall`
3. the user wants study extraction, not just a scouting report

## Workflow

### 1. Get the games

Use the scout pipeline if needed to download public games first:

```bash
python3 skills/chess-opponent-scout/scripts/analyze_player.py <username> scouting/<username> --platform chesscom
```

### 2. Filter for the target opening

Verify the opening from the moves, not from ECO alone.

For French:
- confirm `1. e4 e6`
- classify the variation from the move sequence

For Stonewall:
- confirm the actual Stonewall structure rather than relying on labels

### 3. Keep only instructive games

Prefer games that are:
- long enough to teach something
- won clearly enough to be useful
- rich in thematic moments
- against stronger opposition when possible

### 4. Build the study file

Run:

```bash
python3 skills/chess-opening-study/scripts/build_study.py <username> <french|stonewall> [--max N] [--min-moves M]
```

### 5. Review the result

Before sharing or importing:
- remove weak examples
- make sure the variation mix is sensible
- check that annotations are actually thematic
- verify the PGN headers and links

## Output

Expected output:
- a clean PGN file ready for Lichess study import
- a short summary covering game count, variation mix, and rating range

## Reference ideas used during annotation

French:
- variation-specific plans
- bishop problem handling
- castling choice
- endgame structure awareness

Stonewall:
- move-order discipline
- outpost timing
- bishop management
- pawn-break timing
- kingside attacking plans

## Key files

| File | Purpose |
|------|---------|
| `skills/chess-opening-study/scripts/build_study.py` | Main extraction and annotation script |
| `skills/chess-opponent-scout/scripts/analyze_player.py` | Public game downloader |
| `chess_tools/parse_pgn.py` | PGN parser |

## Critical rules

- verify openings from moves, not from site labels alone
- use a proper PGN parser
- prefer quality over volume
- sort toward the most instructive examples, not just the largest pile of games
