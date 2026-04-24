---
name: chess-concepts
description: "Create and maintain living documents exploring chess concepts (e.g. opposite-side castling, doubling rooks, pawn storms, bishop pair). Each concept is illustrated with chess position diagrams and explored within the context of the current opening systems in use (especially Stonewall and French Defense), using games from Aman Hambleton's speedruns (wonestall/sterkurstrakur), Ju Wenjun, self-account examples supplied at runtime, or scouted opponents. Triggers when user asks to 'make a PDF on [concept]', 'document [concept]', 'chess concept: [topic]', or references updating an existing concept document. NOT for game analysis (use stonewall-coach) or opponent scouting (use chess-opponent-scout)."
---

# Chess Concepts — Living Documents

Create beautiful, illustrated PDFs that teach chess concepts through the lens of the current opening systems in use.

## Trigger

- "Make me a PDF on [concept]"
- "Document [concept]"
- "Chess concept: [topic]"
- "Update the [concept] PDF"
- "Add to the OSC document"

## Existing Concepts

| Concept | File | Generator |
|---------|------|-----------|
| Opposite-Side Castling | `chess-data-private/generated/concepts/opposite-side-castling.pdf` | `chess_tools/concepts/generate_osc.py` |

When adding new concepts, update this table.

## Document Structure (Template)

Every concept PDF follows this pattern:

### 1. Title & Intro
- Bold concept name with emoji
- Subtitle: "A Strategic Framework for [topic]"
- Date + a neutral preparation line
- 2-3 sentence intro framing why this concept matters

### 2. The Laws / Principles (5-12 rules)
Each principle gets:
- **Numbered heading** (LAW I, LAW II, etc. — or PRINCIPLE, RULE, depending on tone)
- **Key text** with bold highlights for critical phrases
- **Chess diagram** illustrating the concept (using `diagram_helpers.py`)
- **Caption** explaining the position

### 3. Opening-Specific Application
How the concept applies within the current systems in use:
- **Stonewall context** — reference wonestall games from the local corpus
- **French context** — reference sterkurstrakur games from the local corpus
- **Cross-reference** with the Stonewall and French guides where relevant

### 4. Real Game Examples
Find illustrative games from:
1. **Primary:** a local corpus PGN (in this repo family, typically `chess-data-private/corpora/games.pgn`)
2. **Secondary:** any supplied side corpus such as Ju Wenjun games
3. **Tertiary:** self-account games only when explicitly supplied at runtime
4. **Scouted opponents:** user-supplied opponent corpora

Search method: use `chess_tools/parse_pgn.py` or the search/query tooling to find games exhibiting the concept. Include lichess/chess.com links.

### 5. Personal or Targeted Note
Tailored advice connecting the concept to the target player's style, strengths, and weaknesses when such a target has been explicitly supplied at runtime.

### 6. Quick Reference Card
Dark background summary box with all principles listed as bullet points.

## Technical Implementation

### Diagram Infrastructure
```python
from diagram_helpers import diagram_html, DIAGRAM_CSS
import chess, chess.svg
```

All diagrams use `chess_tools/diagram_helpers.py`:
- `diagram_html(fen, caption, arrows=None, size=240)` — returns HTML div
- `DIAGRAM_CSS` — CSS to include in stylesheet
- Arrows: `chess.svg.Arrow(from_sq, to_sq, color='#ff0000cc')`

### PDF Generation
- HTML + WeasyPrint (same export stack used for optional Stonewall/French PDFs)
- A4 page size, 20mm margins
- Color scheme: pick a distinct accent color per concept (avoid reusing SW blue or French green)
  - OSC: dark red `#8b0000`
  - Future concepts: pick from `#2c5282` (blue), `#6b21a8` (purple), `#065f46` (green), `#92400e` (amber)

### Generator Script Convention
- File: `chess_tools/concepts/generate_<concept_slug>.py`
- Output: typically `chess-data-private/generated/concepts/<concept-name>.pdf` in this repo family, or another user-supplied output path
- Pre-compute diagrams as variables before the f-string (no backslashes in f-strings)

## Finding Illustrative Games

When building a concept PDF, search for games that demonstrate the concept:

```python
# Example: find all OSC games in a local corpus
from parse_pgn import load_games
wg, bg = load_games('<games.pgn>', 'wonestall')
for g in wg:
    # Check if both sides castled and on different sides
    w_castle = any(m == 'O-O' or m == 'O-O-O' for _, m in g['wm'])
    b_castle = any(m == 'O-O' or m == 'O-O-O' for _, m in g['bm'])
    # ... filter and classify
```

For each illustrative game, include:
- Player names and ratings
- Link to lichess study or chess.com game
- Which move/position best demonstrates the concept
- A diagram of that key moment

## Updating Existing Concepts

When Dash says "update the OSC document" or similar:
1. Read the generator script first
2. Understand current structure
3. Make targeted additions (new examples, refined principles, etc.)
4. Regenerate the PDF
5. Send via message tool

## Key Files

| File | Purpose |
|------|---------|
| `chess_tools/diagram_helpers.py` | Shared diagram rendering (SVG → base64 → HTML) |
| `chess_tools/concepts/` | Concept generators kept in the public repo |
| local corpus PGN (typically `chess-data-private/corpora/games.pgn`) | Primary source material |
| `chess_tools/parse_pgn.py` | PGN parser (MANDATORY) |
| `chess-data-private/generated/stonewall-cheatsheet.pdf` | Optional Stonewall cross-reference in this repo family |
| `chess-data-private/generated/french-cheatsheet.pdf` | Optional French cross-reference in this repo family |

## Critical Rules

- **Always illustrate with diagrams** — no wall-of-text PDFs
- **Always connect to the current opening systems in use** — Stonewall and French context mandatory when relevant
- **Use real games** — not hypothetical positions (when possible)
- **Living documents** — update when new insights emerge
- **Pre-compute diagrams** — define as variables before the f-string to avoid backslash syntax errors
- **Consistent style** — use `chess_tools/diagram_helpers.py` for all diagrams across all concept PDFs
