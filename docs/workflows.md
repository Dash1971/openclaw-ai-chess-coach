# Workflows

## Main workflows in this repo

- study sync and source-list maintenance
- search/query across a chess corpus
- opponent/account scouting
- opening-study extraction from public accounts
- opening concept and study-output generation
- chess.com speedrun PGN extraction for later study ingestion
- scanned puzzle-book transcription into Lichess study chapters

## Generic opening-guide pipeline

The repo now exposes a generic opening pipeline layer in `chess_tools/`:

- `opening_configs.py` — opening registry/configuration
- `tag_opening.py` — generic opening tagger entry point
- `generate_opening_guide.py` — generic guide generator entry point

Current configured openings:
- `stonewall`
- `french`

The older opening-specific scripts still work, but they are no longer the only interface.

Internally, the repo now also has shared helper modules behind those opening-specific implementations:

- `opening_tag_utils.py` — shared tagging helpers such as raw-text extraction, early-move tests, and move-number lookup
- `opening_tag_pipeline.py` — shared tagging execution flow
- `opening_guide_utils.py` — shared guide-render helpers such as game-link rendering and themed game-list sections
- `opening_guide_pipeline.py` — shared guide-output flow

Opening-specific chess knowledge is now being pushed into dedicated modules rather than left in the top-level scripts:

- `stonewall_opening_data.py`
- `french_opening_data.py`
- `stonewall_rules.py`
- `french_rules.py`

Example usage:

```bash
python3 chess_tools/tag_opening.py stonewall --db <games.pgn> --output <output-dir>/stonewall.json
python3 chess_tools/generate_opening_guide.py stonewall --input <output-dir>/stonewall.json --output <output-dir>/stonewall-cheatsheet.pdf
```

```bash
python3 chess_tools/tag_opening.py french --db <games.pgn> --output <output-dir>/french.json
python3 chess_tools/generate_opening_guide.py french --input <output-dir>/french.json --output <output-dir>/french-cheatsheet.pdf
```

## Puzzle-book to study flow

A practical puzzle-book conversion sequence is:

1. rasterize a scanned workbook PDF into high-resolution page images
2. crop each board with rank/file labels visible
3. visually transcribe the pieces and side-to-move prompt
4. run square-occupancy measurement on the crop to catch file/rank mistakes
5. build a legal FEN for each diagram
6. validate the FENs structurally
7. assemble a multi-chapter PGN for Lichess study import

This workflow is documented in more detail at [Puzzle-book to study](puzzle-book-to-study.md).

## Typical study flow

A practical operating sequence is:

1. download speedrun or other public game data
2. import those games into Lichess studies
3. annotate and organize them in Lichess
4. sync the study URLs into a local PGN corpus
5. generate an opening cheat sheet from that annotated corpus with the generic opening-guide pipeline
6. use the openings-coach workflow to critique your own games against the standard set by that cheat sheet
7. scout opponents in advance to estimate how well your preparation is likely to work

This repo ships the public code/docs/examples layer. Keep your real corpus, source manifests, and generated outputs in your own data location.
