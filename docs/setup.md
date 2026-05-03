# Setup

This repo is the public code/docs/examples layer of the chess-assistant stack.

If you are new to OpenClaw itself, start here:
- docs: <https://docs.openclaw.ai>
- source: <https://github.com/openclaw/openclaw>
- community: <https://discord.com/invite/clawd>

## What you need
- Python 3
- an OpenClaw workspace capable of running skill scripts
- for serious use: your own study list and local PGN corpus
- for scanned puzzle-book transcription: `numpy`, `Pillow`, and ideally `pdftoppm`

## What works from this repo alone
- reading the docs
- inspecting the public skills and reusable tooling
- experimenting with the minimal example data in `examples/`

## What should live outside this repo
- your real PGN corpus
- your active study/source manifests
- generated guides, PDFs, and other operating outputs

## What requires your own corpus/study inputs
- full corpus search across a real `games.pgn`
- source-list-driven sync workflows
- large-scale report or study-output generation from your own data
- full puzzle-book transcription from your own workbook PDF scans
