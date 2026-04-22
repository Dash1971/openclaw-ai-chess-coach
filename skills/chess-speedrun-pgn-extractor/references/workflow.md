# Chess.com Speedrun PGN Extractor Workflow

## Goal

Turn a chess.com speedrun account into chunked PGN files suitable for later import into Lichess studies.

## Why this needs confirmation

Speedrun accounts often include:
- setup games before the actual run starts
- older/newer games at different time controls
- resets in rating that mark the real beginning of the series

Do not blindly pull everything.

## Workflow

### 1. Run summary first

Use:
```bash
python3 scripts/extract_speedrun_pgn.py summary <username>
```

Look for:
- likely rating reset points
- dominant time control(s)
- first/last game candidates
- opponent/game that appears to mark the true beginning

### 2. Confirm with the user

Ask concrete questions such as:
- Was `<opponent>` the first speedrun game?
- Was `<opponent>` the last speedrun game?
- Are the speedrun games `5+0` / `3+0` / `15+10`?
- Should older setup games be excluded?

If public metadata from YouTube/video descriptions clearly identifies the start/end/time control, use that to strengthen the proposal — but still confirm if there is ambiguity.

### 3. Extract

Use explicit filters after confirmation, for example:
```bash
python3 scripts/extract_speedrun_pgn.py extract wonestall \
  --start-index 51 \
  --time-control 5+0 \
  --out-dir /tmp/wonestall \
  --prefix wonestall
```

### 4. Report

Report:
- number of games selected
- time control filter used
- first/last retained game by index/opponent
- output file paths

## Output convention

Default chunk size is 64 games per PGN file.

Use filenames like:
- `wonestall_part1.pgn`
- `wonestall_part2.pgn`

## Scope guardrail

This skill is for **extracting and chunking** public chess.com speedrun account games.

It is not for:
- Lichess study syncing itself
- PGN annotation cleanup
- one-off historical remake scripts
