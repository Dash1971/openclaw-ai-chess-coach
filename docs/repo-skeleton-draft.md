# OpenClaw AI Chess Coach — Public Repo Skeleton (Draft)

Status: discussion draft only. No migration executed yet.

## Repo identity

- **Repo name:** `openclaw-ai-chess-coach`
- **License:** MIT
- **Audience:** people who want to understand, run, or adapt an OpenClaw-based chess-coach stack
- **Canonical document model:** markdown-first in GitHub; PDFs are secondary/private exports

## Public repo goals

This repo should present a coherent, generic chess-coach system with:
- reusable chess skills
- reusable chess tooling
- reproducible docs
- minimal example data
- clear boundaries between generic tooling and private operating data

Stonewall, French, and Habits should appear as **example repertoires / example study families**, not as hidden private assumptions.

## Proposed top-level structure

```text
openclaw-ai-chess-coach/
├── README.md
├── LICENSE
├── requirements.txt
├── docs/
│   ├── index.md
│   ├── architecture.md
│   ├── setup.md
│   ├── workflows.md
│   ├── search-system.md
│   ├── opening-families.md
│   ├── data-model.md
│   └── limitations.md
├── skills/
│   ├── openings-coach/
│   ├── chess-opponent-scout/
│   ├── chess-opening-study/
│   ├── chess-concepts/
│   ├── chess-db-sync/
│   └── chess-speedrun-pgn-extractor/
├── chess_tools/
│   ├── parse_pgn.py
│   ├── search.py
│   ├── update_db.py
│   ├── tag_games.py
│   ├── tag_french.py
│   ├── diagram_helpers.py
│   ├── sanitize_pgn_comments.py
│   ├── query_cli.py
│   ├── query_engine.py
│   ├── query_nl.py
│   ├── query_fuzzy.py
│   ├── query_answer.py
│   ├── run_search.py
│   ├── run_query_test.py
│   ├── search_queen_battery.py
│   ├── generate_pdf.py
│   ├── generate_french_pdf.py
│   ├── generate_search_guide_pdf.py
│   └── concepts/
│       └── generate_osc.py
├── examples/
│   ├── README.md
│   ├── sample_games.pgn
│   ├── sample_sources.txt
│   └── example-queries.md
└── scripts/
    └── README.md
```

## Directory purposes

### `docs/`
The canonical browser-readable document layer.

Use this for:
- repo overview
- architecture
- setup / reproducibility
- explanation of example opening families
- search/query docs
- workflow docs
- limitations / assumptions

### `skills/`
The public chess-skill layer.

Keep only skills that are:
- generic enough to publish
- understandable to an outsider
- not tied to one-off historical cleanup

### `chess_tools/`
Canonical generic code layer.

This should contain the real reusable chess tooling, not duplicated staged copies.

### `examples/`
Minimal public sample layer only.

Keep this small and comprehensible:
- one sample PGN
- one sample sources file
- example queries
- maybe one short README explaining how examples relate to the real private data repo

### `scripts/`
Prefer to keep this thin.

If a script is generic, it should usually live under `chess_tools/` or inside a skill. Use `scripts/` only for wrappers that improve usability and cannot be placed more cleanly elsewhere.

## Content rules

### Public repo should contain
- generic skills
- generic chess tooling
- markdown docs
- minimal example data
- public-safe explanatory materials

### Public repo should not contain
- full working corpus (`games.pgn`)
- full source lists used operationally
- generated PDFs as canonical documents
- one-off archive reconstruction scripts
- historical clutter / intermediate PGNs / audit leftovers

## README / inventory rule

The public repo README should include:
- what the repo is
- what it includes
- what it intentionally does not include
- where private companion data lives
- a concise inventory of retained scripts/utilities

Retained generic utilities such as `sanitize_pgn_comments.py` should be documented explicitly, not silently copied in.

## Private companion relationship

The private companion repo `chess-data-private` should hold:
- full `games.pgn`
- full source lists
- generated PDFs
- larger operating data and outputs

The public repo should assume that private repo exists for full-scale operation, while still remaining understandable and partially runnable with its minimal examples.

## Recommended initial doc set

### `README.md`
Front door: overview, features, repo map, quickstart, example-data story, private-companion note.

### `docs/index.md`
Landing page for deeper docs.

### `docs/architecture.md`
How skills, tooling, corpora, and outputs relate.

### `docs/setup.md`
How to install prerequisites and run the basic flows.

### `docs/workflows.md`
How the main workflows fit together:
- sync / search
- game analysis
- opponent scouting
- opening study extraction
- concepts / cheat sheets
- speedrun extraction

### `docs/opening-families.md`
Explain Stonewall / French / Habits as example families and example source layers.

### `docs/data-model.md`
Explain sample data vs private operating data.

### `docs/limitations.md`
Honest boundaries and rough edges.

## Suggested execution rule later

When assembling the clean export tree:
1. prefer canonical versions from `chess-db/` over duplicate staged copies
2. prefer markdown docs over PDF artifacts
3. keep the top-level tree easy to understand in one pass
4. move only minimal examples into `examples/`
5. document every retained script/utility in README or linked docs
