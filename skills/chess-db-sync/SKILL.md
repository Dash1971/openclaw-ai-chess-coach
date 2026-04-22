---
name: chess-db-sync
description: Sync the local chess game database (chess-db/games.pgn) with lichess studies. Triggers when user says "update the game database", "sync the database", "refresh games from lichess", "pull latest annotations", or similar. Covers all studies in chess-db/sources.txt (Stonewall, French, Habits, and any future additions). Compares by ChapterURL — detects new games and updated annotations. NOT for adding entirely new studies (that's a manual append to sources.txt).
---

# Chess DB Sync

Sync `chess-db/games.pgn` with the latest from all lichess studies listed in `chess-db/sources.txt`.

## Workflow

1. Run the sync script:
   ```bash
   python3 chess-db/update_db.py
   ```
   To sync specific studies only:
   ```bash
   python3 chess-db/update_db.py STUDY_ID1 STUDY_ID2
   ```

2. The script:
   - Downloads fresh PGNs from lichess API for each study
   - Compares each game by ChapterURL against the local database
   - Replaces games with updated annotations
   - Appends any new games
   - Creates `games.pgn.bak` backup before writing
   - Reports: new games, updated annotations, unchanged counts

3. After sync, verify integrity:
   ```bash
   grep -c '^\[Event ' games.pgn
   python3 parse_pgn.py games.pgn 2>&1 | tail -5
   ```

4. Report to user: total games updated, notable annotation changes (especially large +char diffs indicating significant new analysis).

## Adding New Studies

When user wants to add a new lichess study to the database:
1. Append the study ID to `chess-db/sources.txt`
2. Run `python3 update_db.py <new_study_id>` to pull it in
3. All future syncs will include the new study automatically

## Notes

- Script rate-limits at 1 second between study downloads (lichess API courtesy)
- Backup is always created before writes
- Game order in the database is preserved
- The script handles 13+ studies with 730+ games efficiently
