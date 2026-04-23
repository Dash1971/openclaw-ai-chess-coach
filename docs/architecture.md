# Architecture

AI Chess Assistant is organized into four main layers:

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

It explains the workflow shape, tool boundaries, and search model.

## 4. Examples

The `examples/` directory is intentionally minimal.

It provides a small sample layer for understanding the workflows without bundling a full working corpus.

## Typical data pipeline

The main study pipeline demonstrated by this project is:

1. gather games from a public source such as chess.com
2. import them into Lichess studies
3. annotate and organize the games inside those studies
4. collect study URLs into a source list
5. sync that source list into a local PGN database
6. run search, coaching, scouting, and document-generation workflows against the local corpus

The repo is generic. You can substitute your own study list, PGN corpus, or import path.
