# Chess Search System

Status: public work-in-progress, but usable.

This repo ships a parser-backed chess search stack inside `chess_tools/`.
It is meant to search a user-supplied PGN corpus deterministically, then let an agent/model translate or explain the results.

Core rule:
- **Python does retrieval**
- **the model translates and explains**
- **the model does not search raw PGN text directly**

## Current files

### Core search engine
- `chess_tools/query_engine.py` — deterministic structured search over a PGN corpus
- `chess_tools/query_fuzzy.py` — fuzzy/scored layer on top of exact search
- `chess_tools/query_cli.py` — raw CLI for exact/fuzzy JSON execution

### Natural-language and answer layers
- `chess_tools/query_nl.py` — rule-first natural-language compiler
- `chess_tools/query_answer.py` — assistant-facing answer wrapper
- `chess_tools/query_backup.py` — more procedural backup wrapper for weaker models

### Supporting search utilities
- `chess_tools/parse_pgn.py`
- `chess_tools/search.py`
- `chess_tools/run_search.py`
- `chess_tools/run_query_test.py`
- `chess_tools/search_queen_battery.py`

## Corpus model

The search stack expects a PGN corpus supplied by the user, for example:
- a local `games.pgn`
- a corpus rebuilt from a Lichess study list via `chess_tools/update_db.py`

This public repo does **not** ship the full working corpus.
It only ships a minimal example layer plus the reusable code.

## Current capabilities

### Exact structured search
Can search by:
- move sequence
- move owner: `self`, `opponent`, `white`, `black`, `any`
- timing windows such as `within_plies`
- board predicates before/after a move

### Supported predicate families
Examples from `query_engine.py` include:
- `piece_on_square`
- `piece_count`
- `piece_defended`
- `move_adds_defender_to_square`
- `move_adds_defender_to_piece`
- `battery`
- `battery_toward_square`
- `piece_attacks_square`
- `rook_on_open_file`
- `rook_on_semi_open_file`
- `rook_lifted`
- `knight_outpost`
- `opposite_side_castling`
- `pawn_storm_against_castled_king`
- `san_contains`

## Practical entry points

### Prefix search
```bash
python3 chess_tools/search.py --db <games.pgn> d4 d5 e3 e6 Bd3
```

### Exact/fuzzy answer wrapper
```bash
python3 chess_tools/query_answer.py "show me exact games with rook lift then rook swing within 8 plies"
python3 chess_tools/query_backup.py "find me a game with a rook lift and queen-rook battery leading to mate"
```

### Raw structured query execution
```bash
python3 chess_tools/query_cli.py --query-file <query.json> --pretty
python3 chess_tools/query_cli.py --fuzzy-file <fuzzy-query.json> --pretty
```

## Scope note

This doc is intentionally public-facing and concise.
It documents the mirrored code that exists in `chess_tools/` today.
If you are rebuilding the full workflow, pair it with your own corpus and source-list files.
