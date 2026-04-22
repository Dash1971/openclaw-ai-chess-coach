---
name: chess-concepts
description: Create and maintain living-document PDFs exploring chess concepts (e.g. opposite-side castling, doubling rooks, pawn storms, bishop pair). Each concept is illustrated with chess position diagrams and explored within the context of the current opening systems in use (especially Stonewall and French Defense), using games from Aman Hambleton's speedruns (wonestall/sterkurstrakur), Ju Wenjun, self-account examples supplied at runtime, or scouted opponents. Triggers when user asks to "make a PDF on [concept]", "document [concept]", "chess concept: [topic]", or references updating an existing concept document. NOT for game analysis (use stonewall-coach) or opponent scouting (use chess-opponent-scout).
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
| Opposite-Side Castling | `chess-db/concepts/opposite-side-castling.pdf` | `chess-db/concepts/generate_osc.py` |

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
- **Stonewall context** — reference wonestall games (105W + 45B in `chess-db/games.pgn`)
- **French context** — reference sterkurstrakur games (60 in `chess-db/games.pgn`)
- **Cross-reference** with the Stonewall and French cheat sheet PDFs where relevant

### 4. Real Game Examples
Find illustrative games from:
1. **Primary:** `chess-db/games.pgn` (Aman's speedruns — wonestall, sterkurstrakur, habitual)
2. **Secondary:** Ju Wenjun games (`ju-wenjun/games.pgn`)
3. **Tertiary:** self-account games only when explicitly supplied at runtime
4. **Scouted opponents:** `opponents/*/games.pgn`

Search method: Use `parse_pgn.py` or grep to find games exhibiting the concept. Include lichess/chess.com links.

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

All diagrams use `chess-db/diagram_helpers.py`:
- `diagram_html(fen, caption, arrows=None, size=240)` — returns HTML div
- `DIAGRAM_CSS` — CSS to include in stylesheet
- Arrows: `chess.svg.Arrow(from_sq, to_sq, color='#ff0000cc')`

### PDF Generation
- HTML + WeasyPrint (same as Stonewall/French PDFs)
- A4 page size, 20mm margins
- Color scheme: pick a distinct accent color per concept (avoid reusing SW blue or French green)
  - OSC: dark red `#8b0000`
  - Future concepts: pick from `#2c5282` (blue), `#6b21a8` (purple), `#065f46` (green), `#92400e` (amber)

### Generator Script Convention
- File: `chess-db/concepts/generate_<concept_slug>.py`
- Output: `chess-db/concepts/<concept-name>.pdf`
- Pre-compute diagrams as variables before the f-string (no backslashes in f-strings)

## Finding Illustrative Games

When building a concept PDF, search for games that demonstrate the concept:

```python
# Example: find all OSC games in the Stonewall database
from parse_pgn import load_games
wg, bg = load_games('games.pgn', 'wonestall')
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
| `chess-db/diagram_helpers.py` | Shared diagram rendering (SVG → base64 → HTML) |
| `chess-db/concepts/` | All concept PDFs and their generators |
| `chess-db/games.pgn` | Aman's speedrun games (primary source) |
| `chess-db/parse_pgn.py` | PGN parser (MANDATORY) |
| `chess-db/stonewall-cheatsheet.pdf` | Cross-reference for SW concepts |
| `chess-db/french-cheatsheet.pdf` | Cross-reference for French concepts |

## Critical Rules

- **Always illustrate with diagrams** — no wall-of-text PDFs
- **Always connect to the current opening systems in use** — Stonewall and French context mandatory when relevant
- **Use real games** — not hypothetical positions (when possible)
- **Living documents** — update when new insights emerge
- **Pre-compute diagrams** — define as variables before the f-string to avoid backslash syntax errors
- **Consistent style** — use `diagram_helpers.py` for all diagrams across all concept PDFs
