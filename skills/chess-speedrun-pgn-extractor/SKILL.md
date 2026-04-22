---
name: chess-speedrun-pgn-extractor
description: Extract a speedrun account's games from chess.com by username, identify the likely speedrun window, confirm the start/end/time-control with the user, and output chunked PGN files suitable for later import into Lichess studies. Use when the user wants to pull a Chessbrah/speedrun account, build a study corpus from a chess.com player, filter out setup games or wrong time controls, or asks for a generic tool to fetch and cut up chess.com speedrun PGNs.
---

# Chess Speedrun PGN Extractor

Use this skill to pull a chess.com account's game history and turn the actual speedrun segment into chunked PGN files.

Read `references/workflow.md` first.

## Core rule

Do not blindly extract everything.

First summarize the account, then confirm the real speedrun window with the user if there is any ambiguity.

## Summary step

Run:
```bash
python3 scripts/extract_speedrun_pgn.py summary <username>
```

Use the summary to identify:
- candidate rating resets
- likely time control
- likely first/last speedrun games

## Confirmation step

If the start/end/time control is not unambiguous from the data alone, confirm with the user using concrete candidate questions.

Examples:
- Was the `fitm-a` game the first game of the speedrun?
- Are the speedrun games `5+0` rather than the earlier/later `3+0` games?
- Should everything before index `N` be excluded?

## Extraction step

After confirmation, extract with explicit filters:
```bash
python3 scripts/extract_speedrun_pgn.py extract <username> \
  --start-index <n> \
  --end-index <m-if-needed> \
  --time-control <5+0|3+0|10+0|15+10> \
  --out-dir <dir> \
  --prefix <name>
```

## Report format

Report back:
- selected username
- chosen start/end boundary
- chosen time control filter
- number of retained games
- output file paths

## Scope guardrails

This skill is for:
- chess.com account history fetch
- speedrun-window detection
- user-confirmed PGN extraction and chunking

This skill is not for:
- Lichess study sync
- annotation cleanup
- one-off remake scripts tied to a historical local corpus
