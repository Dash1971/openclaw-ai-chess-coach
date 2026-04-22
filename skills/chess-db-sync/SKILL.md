---
name: chess-db-sync
description: Sync a local chess PGN database with a maintained list of Lichess studies. Use when a user wants to refresh annotations, pull newly added chapters, or keep a study-backed corpus current.
---

# Chess DB Sync

Use this skill to refresh a local PGN corpus from Lichess studies.

## What it does

- downloads fresh PGNs from the studies you track
- compares games by `ChapterURL`
- replaces games whose annotations changed
- appends newly added games
- keeps a local backup before writing

## Basic workflow

Run the sync script from the repo root:

```bash
python3 chess_tools/update_db.py
```

To sync only specific studies:

```bash
python3 chess_tools/update_db.py STUDY_ID1 STUDY_ID2
```

## Verification

After syncing:

1. check the reported counts for new / updated / unchanged games
2. verify the resulting PGN still parses cleanly
3. spot-check any large annotation changes

## Source-list rule

This skill assumes you maintain a source list for the studies you care about.

When adding a new study:
1. add the study ID to your maintained source list
2. run the sync for that study
3. include it in future full syncs

## Notes

- the sync is designed for incremental upkeep, not one-off historical reconstruction
- treat the synced PGN as generated local data
- verify output before downstream analysis or PDF generation
