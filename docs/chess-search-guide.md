# Chess DB Search Guide

## What this is

The `chess-db/` search system is a query layer over the local PGN database (`games.pgn`).

It is designed to answer questions like:
- *Show me Stonewall White games where Black got a knight to e4.*
- *Find examples of Bxh7+ followed by attacking continuation.*
- *Show similar games with opposite-side castling and a kingside pawn storm.*
- *Find a game with a rook lift, queen-rook battery, and mate.*

The key design rule is:

> **Python does retrieval. The model translates and explains. The model does not search raw PGN text directly.**

---

## Database

Main database file:
- `chess-db/games.pgn`

Current sources in practice include study material from:
- Stonewall
- French
- Habits
- other studies listed in `chess-db/sources.txt`

By default, the system is **opening-agnostic** across the whole PGN database.
It only narrows to Stonewall / French / Habits when the query explicitly asks for that.

---

## Architecture

### 1. Exact retrieval engine
File:
- `chess-db/query_engine.py`

Responsibilities:
- parse PGN with `python-chess`
- build per-move board-state contexts
- evaluate deterministic predicates and move sequences
- return matching games + move windows + reasons

### 2. Fuzzy ranking layer
File:
- `chess-db/query_fuzzy.py`

Responsibilities:
- keep **required** constraints as hard filters
- treat **optional** constraints as ranking signals
- support “similar idea” search without abandoning determinism

### 3. Natural-language compiler
File:
- `chess-db/query_nl.py`

Responsibilities:
- interpret a chess question
- decide exact vs fuzzy mode
- compile the request into structured query JSON / sequence steps
- support motif templates and composed sequence templates

### 4. Human-facing wrapper
File:
- `chess-db/query_answer.py`

Responsibilities:
- run the compiled query
- summarize top matches in a human-readable form
- return study links and brief reasons

### 5. Backup-model wrapper
File:
- `chess-db/query_backup.py`

Responsibilities:
- reduce discretion for weaker backup models (e.g. Kimi)
- use a fixed ladder: parse -> compile -> run -> forced fuzzy fallback -> summarize
- normalize some fuzzy attack-shape wording before search

---

## Technical implementation details

### Core board model
Each move is represented with:
- SAN / UCI move text
- before/after FEN
- before/after `python-chess` board object
- move number and ply
- game metadata (players, study, chapter, URL)

That lets the engine test both:
- **move events**
- **board-state predicates before or after the move**

### Deterministic predicates currently supported
Examples from `query_engine.py`:
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
- `piece_pinned_to_target`
- `opposite_side_castling`
- `pawn_storm_against_castled_king`
- `san_contains`

### Sequence matching
The engine supports ordered sequence steps with:
- move text or regex move text
- side to move (`self`, `opponent`, `white`, `black`, `any`)
- timing windows (`within_plies`)
- attached predicates

This allows searches like:
- `Bxh7+` followed by `Qh5+`
- rook lift followed by rook swing
- opposite-side castling followed by a pawn storm followed by a mating move

### Grouping logic
Motif-only results can otherwise spam adjacent plies from the same game. The engine groups contiguous hits into a single occurrence span and reports:
- occurrence count
- start ply
- end ply

---

## Query modes

### Exact mode
Use when you want literal matches.

Example intent:
- *show me exact Stonewall White games with a black knight on e4*

### Fuzzy mode
Use when you want analogues or similar structures.

Example intent:
- *show me similar games with opposite-side castling and a kingside pawn storm*

---

## Supported motif language
The NL compiler currently understands phrases like:
- `black knight on e4`
- `rook on open e-file`
- `rook on semi-open c-file`
- `bishop pointed at h7`
- `queen-bishop battery toward h7`
- `knight outpost on e5`
- `knight pinned to king on f6`
- `opposite-side castling`
- `pawn storm against kingside castled king`
- `rook lift`
- `rook swing to g3`
- `bishop sac on h7`

### Composed templates
Also supported:
- `rook lift then rook swing within 8 plies`
- `bishop sac on h7 and attacking continuation within 6 plies`
- `opposite-side castling, pawn storm, and heavy-piece follow-up`

### Backup normalization
The backup wrapper normalizes sloppy phrasing like:
- `rook uplift` -> `rook lift`
- `queen rook battery` -> `queen-rook battery`
- `leading to checkmate` -> `mate finish`

---

## Recommended CLI usage

### Best normal entry point
```bash
python3 chess-db/query_answer.py "<natural language chess question>"
```

### Best backup-model entry point
```bash
python3 chess-db/query_backup.py "<natural language chess question>"
```

### Debug how the question was interpreted
```bash
python3 chess-db/query_nl.py "<question>" --parse-only
python3 chess-db/query_nl.py "<question>" --compile-only
```

### Run raw exact JSON
```bash
python3 chess-db/query_cli.py --query-file chess-db/examples-queen-battery.json --pretty
```

### Run raw fuzzy JSON
```bash
python3 chess-db/query_cli.py --fuzzy-file chess-db/examples-fuzzy-queen-battery-black.json --pretty
```

---

## Practical examples

### Example 1 — Black knight on e4 in Stonewall White games
```bash
python3 chess-db/query_answer.py "show me stonewall white games with a black knight on e4" --limit 5
```

### Example 2 — Greek Gift pattern
```bash
python3 chess-db/query_answer.py "show me similar stonewall games with bishop sac on h7" --limit 5
```

### Example 3 — Rook lift into rook swing
```bash
python3 chess-db/query_answer.py "show me exact games with rook lift then rook swing within 8 plies" --limit 3
```

### Example 4 — Opposite-side castling attack shape
```bash
python3 chess-db/query_answer.py "show me similar games with opposite-side castling and pawn storm against kingside castled king" --limit 5
```

### Example 5 — Backup wrapper for fuzzy attack prose
```bash
python3 chess-db/query_backup.py "find me a game with a rook uplift which resulted in a queen rook battery leading to a checkmate" --limit 3
```

Known validated candidate from that class of query:
- `wonestall vs fitm-a`
- <https://lichess.org/study/jjmB1AcS/XkWrws5O>

---

## Known limitations

- If the prompt is too vague, the system should ask for clarification instead of inventing precision.
- Prompts like `e4` may be misread as the **move** `e4` rather than the **square** `e4`; better wording is `black knight on e4`.
- `attacking continuation` and `heavy-piece follow-up` are deterministic but still broad unless the prompt narrows them.
- `rook lift` is intentionally broad: it means a materially advanced rook, not necessarily a textbook third-rank lift.
- Backup models are more reliable through `query_backup.py` than by freehand orchestration.

---

## File map

Main docs:
- `chess-db/SEARCH_SYSTEM.md`
- `chess-db/assistant_query_workflow.md`
- `chess-db/KIMI_BACKUP_WORKFLOW.md`
- `chess-db/query_examples.md`
- `chess-db/fuzzy_query_examples.md`
- `chess-db/nl_query_examples.md`
- `chess-db/attack_shape_examples.md`
- `chess-db/castling_attack_examples.md`
- `chess-db/relation_template_examples.md`

Main executables:
- `chess-db/query_answer.py`
- `chess-db/query_backup.py`
- `chess-db/query_nl.py`
- `chess-db/query_cli.py`
- `chess-db/query_engine.py`
- `chess-db/query_fuzzy.py`

---

## Bottom line

This is no longer just an opening-prefix search.
It is now a structured local chess query system with:
- deterministic board-state retrieval
- motif and relation search
- fuzzy ranking
- composed attack-pattern search
- a backup path for weaker models

For day-to-day use, start with:

```bash
python3 chess-db/query_answer.py "<question>"
```

For backup-model resilience, start with:

```bash
python3 chess-db/query_backup.py "<question>"
```
