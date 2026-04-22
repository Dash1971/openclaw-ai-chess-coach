# Working update flow

This is the plain update flow for the staged private repo.

## 1. Update the study database

Purpose: keep the local opening corpus in sync with the Lichess study list.

Command:

```bash
python3 scripts/update_db.py
```

Inputs:

- `data/study-db/sources.txt`
- current `data/study-db/games.pgn`

Output:

- updated `data/study-db/games.pgn`
- `.bak` backup file next to it

## 2. Search the study database

Purpose: find matching games by move prefix.

Small sample:

```bash
python3 scripts/search.py e4 e6 d4 d5 exd5 exd5 Nc3 Nf6
```

Full staged database:

```bash
python3 scripts/search.py --db data/study-db/games.pgn e4 e6 d4 d5 exd5 exd5 Nc3 Nf6
```

## 3. Run game-analysis prep

Purpose: prepare Stonewall or French reference data before writing a coach-style analysis.

Stonewall tags:

```bash
python3 scripts/tag_games.py
```

French tags:

```bash
python3 scripts/tag_french.py
```

These commands write tagged JSON to `/tmp/` for the PDF generators and for manual analysis work.

## 4. Regenerate the opening cheat sheets

Stonewall:

```bash
python3 scripts/tag_games.py
python3 scripts/generate_stonewall_pdf.py
```

French:

```bash
python3 scripts/tag_french.py
python3 scripts/generate_french_pdf.py
```

Outputs:

- `artifacts/stonewall-cheatsheet.pdf`
- `artifacts/french-cheatsheet.pdf`

## 5. Refresh an opponent report

Download a player’s games:

```bash
python3 scripts/analyze_player.py <username> tmp/<username> --platform chesscom
```

Current note:

- the analysis engine is general
- personalized staged report samples were removed from the mirrored repo
- the next cleanup target for this feature is a generic report-rendering layer

## 6. Review before any public split

Before copying anything into a public repo:

- decide which feature is being published
- remove unrelated local/generated staging files
- run a PII/publication audit
- prefer a fresh public repo over flipping this staging repo public
