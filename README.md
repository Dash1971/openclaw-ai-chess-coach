# AI Chess Assistant

AI Chess Assistant is a generic OpenClaw-based chess study stack for building your own local chess assistant around reusable skills, reusable tooling, and a small example layer.

It is designed to support workflows such as:
- syncing annotated Lichess studies into a local PGN corpus
- searching a local chess database by structure, motif, or sequence
- opponent scouting from public account histories
- extracting opening-study material from public accounts
- generating concept documents and other study outputs from tagged games
- pulling speedrun games from chess.com for later study import

---

## What is OpenClaw?

[OpenClaw](https://github.com/openclaw/openclaw) is the agent runtime this project is built around.

If you are coming to this repo fresh, the basic idea is:
- OpenClaw provides the agent, tool, session, and automation framework
- this repo provides a chess-specific layer on top of that framework
- the chess layer adds study-sync, search, scouting, and analysis workflows

Useful links:
- docs: <https://docs.openclaw.ai>
- source: <https://github.com/openclaw/openclaw>
- community: <https://discord.com/invite/clawd>

---

## How the source-material pipeline works

A typical workflow looks like this:

1. pull games from a public source such as a chess.com speedrun account
2. import those games into one or more Lichess studies
3. annotate and organize the games in Lichess
4. collect the study URLs into a source list
5. sync those studies into a local PGN database
6. run search, coaching, scouting, and document-generation workflows against that local corpus

You do not have to use this exact pipeline, but it is the main workflow this repo demonstrates.

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
- document/export generators

### Docs
The `docs/` tree explains the architecture, setup, workflows, and search system.

### Examples
The `examples/` tree is intentionally small:
- sample PGN
- sample source list
- example commands and prompts

The example layer is there to show structure and usage, not to act as a full working corpus.

---

## Example opening families

Stonewall, French, and Habits appear here as example study families built from public speedrun material.

They are examples of how to organize and query a repertoire corpus, not hardcoded requirements for using the tooling.

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
Browser-readable documentation.

### `skills/`
Reusable chess workflows.

### `chess_tools/`
Reusable implementation code.

### `examples/`
Minimal sample inputs and example commands.

---

## Intended use

This repo is meant to help a public user understand and rebuild the system shape:
- how source games are gathered
- how annotated studies become a local corpus
- how that corpus is queried and turned into reports or study documents

For full-scale use, point the tools at your own study list and your own local PGN corpus.
