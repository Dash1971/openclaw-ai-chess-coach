# Architecture

OpenClaw AI Chess Coach is organized into four main layers:

## 1. Skills

The `skills/` directory holds the high-level chess workflows, such as:
- opening analysis and coaching
- opponent/account scouting
- opening-study extraction
- chess concept maintenance
- study-database sync
- chess.com speedrun PGN extraction

## 2. Chess tools

The `chess_tools/` directory holds the reusable implementation code behind those workflows, including:
- PGN parsing
- search/query logic
- tagging helpers
- study-sync helpers
- diagram helpers
- small PGN sanitation utilities
- document/export generators

## 3. Docs

The `docs/` directory is the canonical browser-readable documentation layer.

The long-term direction is markdown-first documentation that can be reviewed directly in GitHub.

## 4. Examples

The `examples/` directory is intentionally minimal.

It provides a small sample layer for understanding the workflows without bundling the full operating corpus.

## Private companion relationship

This public repo is the generic, publishable layer.

The private companion repo `chess-data-private` holds the full working corpus, full source lists, and private generated outputs used in day-to-day operation.
