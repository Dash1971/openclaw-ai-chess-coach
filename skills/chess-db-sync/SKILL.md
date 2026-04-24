---
name: chess-db-sync
description: Sync a local chess PGN corpus with lichess studies. Triggers when user says "update the game database", "sync the database", "refresh games from lichess", "pull latest annotations", or similar. Uses `chess_tools/update_db.py`, compares by ChapterURL, and detects new games plus updated annotations. NOT for adding entirely new studies blindly — update the source manifest deliberately.
---

# Chess DB Sync

Sync a local PGN corpus with the latest from a Lichess study list.

In this repo family, the usual split is:
- code in `chess_tools/`
- private source list and corpus in `chess-data-private`

Typical paths for Dash's setup are:
- source list: `chess-data-private/sources/merged-sources.txt`
- corpus: `chess-data-private/corpora/games.pgn`

## Workflow

1. Run the sync script with explicit paths:
   ```bash
   python3 chess_tools/update_db.py --sources <sources.txt> --db <games.pgn>
   ```
   To sync specific studies only:
   ```bash
   python3 chess_tools/update_db.py --db <games.pgn> STUDY_ID1 STUDY_ID2
   ```

2. The script:
   - downloads fresh PGNs from the lichess API for each study
   - compares each game by `ChapterURL` against the local database
   - replaces games with updated annotations
   - appends any new games
   - creates a `.bak` backup before writing
   - reports: new games, updated annotations, unchanged counts

3. After sync, verify integrity:
   ```bash
   grep -c '^\[Event ' <games.pgn>
   python3 chess_tools/parse_pgn.py <games.pgn> 2>&1 | tail -5
   ```

4. Report to user: total games updated, notable annotation changes (especially large `+char` diffs indicating significant new analysis).

## Adding New Studies

When the user wants to add a new lichess study to the database:
1. append the study ID to the source manifest (for this repo family, typically `chess-data-private/sources/merged-sources.txt`)
2. run `python3 chess_tools/update_db.py --db <games.pgn> <new_study_id>` to pull it in
3. all future syncs using that manifest will include the new study automatically

## Notes

- Script rate-limits at 1 second between study downloads (lichess API courtesy)
- Backup is always created before writes
- Game order in the database is preserved
- The public repo provides the code; the real operating corpus/source list normally lives in the private companion repo or a user-supplied data path
