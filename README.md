# OpenClaw AI Chess Coach

OpenClaw AI Chess Coach is a generic OpenClaw-based chess analysis and training stack built around reusable chess skills, reusable chess tooling, and lightweight example data.

It is designed to support workflows such as:
- opening study sync and search
- game analysis against a local corpus
- opponent scouting
- opening-study extraction from public accounts
- concept and cheat-sheet generation
- speedrun account PGN extraction from chess.com

This public repo is the **generic, publishable** layer.

It does **not** contain the full working corpus or the full set of generated outputs used in day-to-day operation. Those live in a separate private companion repo.

---

## What this repo includes

### Skills
- `openings-coach` — opening-oriented analysis and coaching workflows
- `chess-opponent-scout` — generic username-driven opponent/account scouting
- `chess-opening-study` — extract and shape opening-study material
- `chess-concepts` — maintain concept documents around recurring opening themes
- `chess-db-sync` — sync study-based source material into the local database layer
- `chess-speedrun-pgn-extractor` — fetch and chunk chess.com speedrun account games for later study ingestion

### Chess tools
The `chess_tools/` layer contains the reusable code behind the workflows, including:
- PGN parsing
- search/query logic
- study sync logic
- tagging helpers
- diagram helpers
- PGN comment sanitation helpers
- PDF/document generators where markdown has not yet fully replaced export-oriented flows

### Docs
The `docs/` tree is the canonical documentation layer.

The long-term direction is **markdown-first documentation** that can be read and reviewed directly in GitHub.

### Minimal example data
The `examples/` tree holds a small public-safe sample layer only:
- sample PGN
- sample source list
- example queries

This repo is intentionally not bundled with the full operating corpus.

---

## Example opening families

The repo uses the following as **example repertoires / example study families**:
- Stonewall
- French
- Habits

These are included as examples of how the system can be organized and studied.

They should not be read as hidden assumptions that the code only works for one private setup.

---

## What this repo does not include

This public repo intentionally does not include:
- the full working `games.pgn` corpus
- the full operational source list set
- generated PDFs as canonical source documents
- one-off historical reconstruction scripts
- historical archive clutter and intermediate import artifacts

Those belong either in the private data companion repo or in the retire/drop bucket.

---

## Private companion repo

The private companion repo is:
- `chess-data-private`

That repo is intended to hold:
- full corpus data
- full source lists
- generated PDFs and other working outputs
- larger operating data that should stay private while still being synced for recovery/review

---

## Repository layout

```text
README.md
LICENSE
requirements.txt
docs/
skills/
chess_tools/
examples/
```

### `docs/`
Browser-readable canonical docs.

### `skills/`
Public chess skills.

### `chess_tools/`
Canonical reusable chess tooling.

### `examples/`
Minimal public sample layer.

---

## Documentation rule

Retained generic utilities should be documented, not silently copied in.

That includes small utilities such as:
- `sanitize_pgn_comments.py`

as well as the larger headline tools.

---

## Current direction

The long-term direction for this project is:
- generic public repo for code, skills, docs, and minimal examples
- private companion repo for the real working data layer
- markdown-first docs, PDF-second

This keeps the project readable in GitHub while still preserving the full operating data separately.
