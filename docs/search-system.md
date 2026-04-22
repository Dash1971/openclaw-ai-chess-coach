# Chess DB Search System

Status: active work-in-progress, but usable now.

This file is the durable handoff doc for the new chess search stack.
It is meant for future sessions, resets, and other models.

## Purpose

The old `search.py` only did opening-prefix matching.
The new system supports:
- exact structured motif/position search
- fuzzy/similarity-style search with optional weighted motifs
- natural-language compilation into structured queries
- assistant-facing human-readable answers
- grouped motif-only results so one sustained motif stretch does not spam adjacent plies as separate results

Core rule:
- **Python does retrieval**
- **the model translates and explains**
- **the model does not search raw PGN text directly**

---

## Files

### Core engine
- `chess-db/query_engine.py`
  - deterministic structured search over `games.pgn`
  - parses PGN with `python-chess`
  - supports move sequences + board predicates

- `chess-db/query_fuzzy.py`
  - fuzzy layer on top of exact search
  - required steps = hard constraints
  - optional steps = scoring/ranking signals

- `chess-db/query_cli.py`
  - raw CLI for exact/fuzzy JSON execution

### Natural-language and assistant layers
- `chess-db/query_nl.py`
  - rule-first NL -> exact/fuzzy query compiler
  - extracts players, color, study hints, SAN moves, square facts, motif phrases
  - returns `needs_clarification` if the prompt is too vague

- `chess-db/query_answer.py`
  - assistant-facing wrapper
  - takes a normal chess question
  - runs the NL/compiler/search stack
  - returns compact human-readable results instead of raw JSON

- `chess-db/query_backup.py`
  - procedural backup wrapper for weaker/backup models
  - forces a fixed ladder: normalize fuzzy attack wording -> parse/compile/run -> attack-shape fallback -> forced fuzzy fallback -> summarize
  - preferred first entry point for Kimi-style backup operation

### Docs/examples
- `chess-db/query_examples.md`
- `chess-db/fuzzy_query_examples.md`
- `chess-db/query_translation_prompt.md`
- `chess-db/nl_query_examples.md`
- `chess-db/nl_query_test_prompts.md`
- `chess-db/motif_template_examples.md`
- `chess-db/assistant_query_workflow.md`

---

## Current capabilities

### Exact structured search
Can search by:
- move sequence
- move owner: `self`, `opponent`, `white`, `black`, `any`
- timing windows: `within_plies`
- board predicates before/after a move

### Supported predicates
From `query_engine.py`:
- `piece_on_square`
- `piece_count`
- `piece_defended`
- `move_adds_defender_to_square`
- `move_adds_defender_to_piece`
- `battery`
- `piece_attacks_square`
- `rook_on_open_file`
- `rook_on_semi_open_file`
- `knight_outpost`
- `battery_toward_square`
- `piece_pinned_to_target`
- `opposite_side_castling`
- `pawn_storm_against_castled_king`
- `rook_lifted`
- `san_contains`

### Fuzzy search
- required steps are executed as the exact backbone
- optional steps influence ranking only
- useful for prompts like:
  - "similar ideas"
  - "closest analogues"
  - "same concept in another position"

### NL wrapper currently understands
- players: `wonestall`, `sterkurstrakur`, `habitual`, plus any additional usernames present in the local corpus
- `Aman` + opening hint:
  - stonewall -> `wonestall`
  - french -> `sterkurstrakur`
  - habits -> `habitual`
- colors: `as white`, `as black`, `white games`, `black games`
- study/opening hints: `stonewall`, `french`, `habits`, `london`
- SAN moves like `Qc7`, `Nbd7`, `Bxh7+`, `O-O`
- square facts like `white knight on e5`, `bishop on d6`
- motif phrases like:
  - `battery`
  - `defend/protect/stabilize/support`
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
- composed sequence templates like:
  - `rook lift then rook swing within 8 plies`
  - `bishop sac on h7 and attacking continuation`
  - `opposite-side castling, pawn storm, and heavy-piece follow-up`

---

## Known limitations

This is still narrow and deliberate.

It is **good** at:
- anchor-move searches
- square-fact searches
- deterministic motif checks
- exact vs fuzzy routing
- grouped motif-only hits into contiguous occurrence spans per game
- deterministic multi-step attack-shape expansion into ordinary query steps

It is **not yet good** at:
- broad positional prose with no anchors
- rich piece relations like pins/x-rays unless encoded explicitly
- semantic chess plans with no move/square hook
- relative ownership words like `my bishop` when no player anchor exists

Important behavior:
- if no player is known, `self/opponent` semantics degrade to `any`
- vague prompts should return clarification, not fabricated precision
- backup models should prefer `query_backup.py` over ad-hoc orchestration
- backup wrapper now canonicalizes fuzzy attack wording like `rook uplift`, `queen+rook battery`, `heavy-piece battery`, and `leading to checkmate` before search

---

## Recommended usage

### Best chat-facing entry point
Use:
```bash
python3 chess-db/query_answer.py "<natural language chess question>"
```

### Best backup-model entry point
Use:
```bash
python3 chess-db/query_backup.py "<natural language chess question>"
```

For fuzzy attack-shape prose, the backup wrapper now applies three extra normalization/interpretation passes before giving up:
- `rook uplift` / `rook uplifted` / `lifted rook` -> `rook lift`
- `queen rook battery` / `queen+rook battery` / `heavy-piece battery` -> `queen-rook battery`
- `leading to checkmate` / `mate` / `mating finish` -> `mate finish`

If that normalized text contains the full trio `rook lift + queen-rook battery + mate finish`, the wrapper compiles a deterministic sequence:
1. rook-lift predicate
2. queen-behind-rook battery predicate within 12 plies
3. mating move regex (`.*#`) within 12 plies

See also:
- `chess-db/KIMI_BACKUP_WORKFLOW.md`

### For debugging translation
Use:
```bash
python3 chess-db/query_nl.py "<question>" --parse-only
python3 chess-db/query_nl.py "<question>" --compile-only
```

### For raw JSON execution
Use:
```bash
python3 chess-db/query_cli.py --query-file <file.json> --pretty
python3 chess-db/query_cli.py --fuzzy-file <file.json> --pretty
```

---

## Example queries

### Exact
```bash
python3 chess-db/query_answer.py "show me exact wonestall black games where Qc7 came before Nbd7 with a white knight on e5"
```

### Fuzzy
```bash
python3 chess-db/query_answer.py "show me similar wonestall black games where Qc7 stabilized the bishop before Nbd7 with a bishop on d6"
```

### Motif template
```bash
python3 chess-db/query_answer.py "show me exact black games with a knight outpost on e4"
```

### Composed attack-shape template
```bash
python3 chess-db/query_answer.py "show me exact games with rook lift then rook swing within 8 plies"
python3 chess-db/query_answer.py "show me exact games with bishop sac on h7 and attacking continuation within 6 plies"
python3 chess-db/query_answer.py "show me exact games with opposite-side castling, pawn storm, and heavy-piece follow-up"
python3 chess-db/query_backup.py "find me a game with a rook uplift which resulted in a queen rook battery leading to a checkmate"
```

---

## Next planned work

Most valuable next additions:
- better ownership resolution for `my/their` in non-player-anchored prompts
- richer relation templates beyond square-targeted ones (pawn chains, weak-color complexes, exchange-sac structures)
- better grouping heuristics so motif spans cluster by structural phase, not just contiguous plies
- narrower continuation semantics for composed templates when the prompt is still broad (for example, stronger definitions of `attacking continuation` and `heavy-piece follow-up`)

---

## Recovery note for future sessions

If a session resets mid-task:
1. read this file first
2. use `query_answer.py` to test whether the stack still runs
3. use `query_nl.py --compile-only` on the failing prompt to see whether the problem is parsing or retrieval
4. if results look noisy, inspect `query_engine.py` predicates before changing the NL layer
