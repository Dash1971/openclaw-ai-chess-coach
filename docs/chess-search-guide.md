# Chess Search Guide

## What this is

This repo ships a parser-backed search system inside `chess_tools/` for querying a user-supplied PGN corpus.

It is designed to answer questions like:
- *Show me Stonewall games where Black got a knight to e4.*
- *Find examples of Bxh7+ followed by attacking continuation.*
- *Show similar games with opposite-side castling and a kingside pawn storm.*
- *Find a game with a rook lift, queen-rook battery, and mate.*

The key design rule is:

> **Python does retrieval. The model translates and explains. The model does not search raw PGN text directly.**

## Inputs

Typical inputs are:
- a local `games.pgn`
- a study source list for rebuilding that corpus via `chess_tools/update_db.py`

The public repo does not ship the full working corpus. It ships the code plus a small example layer.

## Main files

### Search engine
- `chess_tools/query_engine.py`
- `chess_tools/query_fuzzy.py`
- `chess_tools/query_cli.py`

### NL / answer wrappers
- `chess_tools/query_nl.py`
- `chess_tools/query_answer.py`
- `chess_tools/query_backup.py`

### Supporting tools
- `chess_tools/parse_pgn.py`
- `chess_tools/search.py`
- `chess_tools/run_search.py`
- `chess_tools/run_query_test.py`

## What the system can do

### Exact search
Can search by:
- move sequence
- side to move
- timing windows
- board-state predicates before/after a move

### Fuzzy search
Can keep required constraints hard while treating the rest as ranking signals.

### Natural-language compilation
Can interpret a chess question, decide whether it should be exact or fuzzy, and compile it into structured search input.

## Practical commands

### Prefix search
```bash
python3 chess_tools/search.py --db <games.pgn> d4 d5 e3 e6 Bd3
```

### Answer wrapper
```bash
python3 chess_tools/query_answer.py "show me exact games with rook lift then rook swing within 8 plies"
```

### Backup wrapper
```bash
python3 chess_tools/query_backup.py "find me a game with a rook lift and queen-rook battery leading to mate"
```

### Raw structured query CLI
```bash
python3 chess_tools/query_cli.py --query-file <query.json> --pretty
python3 chess_tools/query_cli.py --fuzzy-file <fuzzy-query.json> --pretty
```

## Scope note

This is the public/browser-readable guide, not an internal handoff dump.
It documents the mirrored `chess_tools/` layer as it exists in this repo today.
