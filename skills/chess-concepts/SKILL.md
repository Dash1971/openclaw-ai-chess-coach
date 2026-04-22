---
name: chess-concepts
description: Create and maintain concept documents around recurring chess ideas such as opposite-side castling, pawn storms, bishop pairs, or rook lifts. Use when the goal is to teach a concept with diagrams, examples, and opening-specific context.
---

# Chess Concepts

Use this skill to build **concept documents** that explain a strategic idea through:
- principles
- diagrams
- real game examples
- opening-specific application

## Good use cases

- “make a PDF on opposite-side castling”
- “document rook lifts”
- “add examples to the pawn storm concept sheet”

## Document pattern

Each concept document should usually contain:

1. a short introduction
2. a set of core principles or laws
3. illustrative diagrams
4. application inside relevant opening families
5. real game examples
6. a compact quick-reference summary

## Source priority

Use examples from:
1. the local main corpus
2. other public example collections supplied by the project
3. explicitly supplied target-player games when relevant

## Opening context

When relevant, connect the concept to example opening families such as:
- Stonewall
- French
- Habits

These are examples, not hard limitations.

## Diagram workflow

Use the shared helpers in:
- `chess_tools/diagram_helpers.py`

If you generate PDFs locally, keep the output workflow consistent and verify the diagrams actually illustrate the intended idea.

## Generator conventions

When maintaining generator scripts:
- keep concept generators under a predictable path
- keep outputs reproducible
- pre-compute diagrams cleanly before assembling large HTML strings

## Updating an existing concept

When revising a concept document:
1. read the existing generator first
2. understand the current structure
3. add or revise examples deliberately
4. regenerate locally
5. verify the result before sharing it

## Critical rules

- use real games whenever practical
- illustrate ideas with diagrams, not just prose
- connect the concept to concrete opening play when that helps
- keep the document focused on one strategic idea rather than mixing many themes
