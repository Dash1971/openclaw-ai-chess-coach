# Study DB sync + search

## What it does

This workflow keeps a local PGN database in sync with a list of Lichess studies and lets you search the resulting corpus by move prefix.

## Main files

- `chess_tools/update_db.py`
- `chess_tools/parse_pgn.py`
- `chess_tools/search.py`

## Typical pipeline

1. maintain a list of Lichess study IDs or URLs
2. download the current study PGNs
3. match games by `ChapterURL`
4. replace updated games, append new games, and keep order stable
5. search the resulting PGN with parser-backed move-prefix search

## Example commands

Sync a study list into a local database:

```bash
python3 chess_tools/update_db.py --sources <sources.txt> --db <games.pgn>
```

Search a local PGN corpus:

```bash
python3 chess_tools/search.py --db <games.pgn> d4 d5 e3 e6 Bd3
```

## Notes

- the public repo ships only a small sample layer for understanding the workflow
- full-scale use expects your own study list and your own local PGN corpus
- `update_db.py` now expects explicit `--sources` and `--db` paths unless you keep those files next to the script
- the search path is parser-backed, not regex-only, so it can survive comments and PGN clutter more reliably
