---
name: openings-coach
description: Analyze chess games against Aman Hambleton's speedrun databases (Stonewall and French Defense). Triggers when user sends a PGN file or chess game for analysis, asks about Stonewall or French opening strategy, references "our SW PDF" or "French PDF", or requests updates to either living document. Also triggers on questions about wonestall/sterkurstrakur/Aman's speedrun patterns. NOT for general chess questions unrelated to these openings, or for the chess-db move prefix search (that's a separate trigger).
---

# Opening Coach (Stonewall + French)

## Opening Detection

When Dash sends a PGN file, detect the opening BEFORE analyzing:

1. Parse with `chess-db/parse_pgn.py` (NEVER one-line regex)
2. Classify the opening:

**Stonewall Detection (White or Black):**
- White SW: d4 + e3 + f4 + Bd3 structure (any order)
- Black SW: d5 + e6 + f5 + Bd6 structure (typically vs 1.d4)
- Reference player: **wonestall** | DB: current local Stonewall corpus in `chess-db/games.pgn`
- Before Stonewall-specific analysis or PDF work, read `skills/openings-coach/references/stonewall-notes.md`

**French Defense Detection:**
- 1.e4 e6 (as Black) — any variation (Winawer, Exchange, Advanced, Tarrasch, sidelines)
- Reference player: **sterkurstrakur** | DB: 60 Black games
- Sub-classify variation using chapter name + moves (see `tag_french.py` for classification logic)

**If neither:** Still analyze the game, but note that no speedrun reference database applies. Offer general observations only.

**If ambiguous (e.g. French Exchange → Stonewall attempt):** Flag both contexts. The French PDF documents that SW in exchange doesn't scale — mention this.

---

## Mode 1: Game Analysis (PGN received)

### Step 1: Parse & Detect
```bash
cd <workspace>/chess-db
python3 -c "
from parse_pgn import load_games
# Load both reference databases
sw_white, sw_black = load_games('games.pgn', 'wonestall')
_, french_games = load_games('games.pgn', 'sterkurstrakur')
print(f'Stonewall: {len(sw_white)} White, {len(sw_black)} Black')
print(f'French: {len(french_games)} games')
"
```

### Step 2: Analyze by Opening

---

#### STONEWALL ANALYSIS

**Opening (moves 1-8):**
- Move order: Does it match wonestall's typical sequences?
- White: d4→e3→Bd3 (move 3 in 61% of games)→f4. Was Bd3 prioritized?
- Black: Pawns before pieces? (76% play 4+ pawns first). Was wall completed before developing?
- Black vs London: Did they play early Bd6 to challenge Bf4?
- Black vs d4+c4+Nc3: f5 before c6 is Aman's choice (5/6 games)

**Middlegame (moves 8-20):**
- White: Ne5 played? (76% of wonestall games). Nd2 for d4 protection? (82%)
- Black: Ne4 played? (81% — THE primary plan). When? (avg move 11)
- Bad bishop: White DSB maneuver attempted? Black LSB maneuver (Bd7→Be8→Bh5)?
- Did they fear opponent knight intrusions? (Aman tolerates Ne5 in 45% of Black games)
- Queen deployment: White Qf3/Qh5? Black Qe8 reroute?

**Tactical moments:**
- Were concrete advantages missed for strategic plans?
- Bxh7+ Greek gift opportunities? (12% of White games)
- g4 storm timing? e4 break timing?

**Stonewall Report Card Principles:**
| Principle | What to check |
|-----------|--------------|
| Move order | Bd3 timing (White) / pawns-first (Black) |
| Knight outpost | Ne5 (White) / Ne4 (Black) — timing and commitment |
| Nd2 support | Did d4 get adequate protection? (White) |
| Bad bishop | Maneuver attempted or bishop stuck? |
| King safety | Castling timing (~move 8 is Aman's avg) |
| Pawn breaks | g4/e4 (White) or g5/e4 (Black) — timing and preparation |
| Strategic patience | Buildup vs premature tactics |

---

#### FRENCH DEFENSE ANALYSIS

**Variation identification (first 5-10 moves):**
- Winawer (Bb4 after Nc3 — Aman plays this 100% of the time)
- Exchange (exd5 exd5 — symmetrical, three sub-plans)
- Advanced (e5 — chain attack needed)
- Tarrasch (Nd2 — c5 response)
- Sidelines (KIA, etc.)

**The Bad LSB — THE central problem (check which solution was used):**
- Ba6 trade (Winawer plan: b6→Ba6, trade the problem piece)
- Diagonal development (Bg4/Bf5/Be6 — exchange variation)
- Bd7→Bb5 (advanced variation maneuver)
- Made irrelevant (endgame — if game simplified, was LSB a non-factor?)

**Variation-specific checks:**

*Exchange:*
- Which of the three plans? Decision tree: SW attempt → Aggressive O-O-O → Conservative O-O
- SW attempt warning: "will not scale" — was this tried? Did it work? Why/why not?
- Opponent disruptions: Qe2+, Nc3, c4, Re1+, Bg5 — how were they handled?
- f6 response to Bg5? (Aman: "wanted anyway" — controls e5/g5, prepares storm)

*Advanced:*
- Qb6+Nc6+c5 pressure on d4? (THE plan)
- b2 blunder pattern — was it available? (6 games in DB where opponent drops b2)
- Ne7→f5 break timing?
- Chain attack executed or stalled?

*Winawer:*
- b6→Ba6 trade executed?
- Nxa6→Nb8→Nc6 knight reroute? (the elegant repositioning)
- h5 counter if opponent attacks kingside?
- Awareness of Qg4 threats?

**Middlegame/Endgame:**
- Castling choice: KS (60%), QS (17%), never (23%) — was the choice appropriate?
- Knight vs bad bishop endgame? (15-game recurring theme — strong for French player)
- Pawn color strategy in endgames?

**French Report Card Principles:**
| Principle | What to check |
|-----------|--------------|
| LSB solution | Was the bad bishop addressed with the right method for the variation? |
| Variation plan | Did they follow the correct plan for the variation encountered? |
| Chain attack | (Advanced) Was the pawn chain attacked at the base? |
| Exchange plan selection | (Exchange) SW→Aggressive→Conservative decision tree followed? |
| Opponent disruptions | Were common disruptions (Nc3/Qe2+/c4/Re1+) handled per Aman's patterns? |
| Castling decision | Appropriate for the position type? |
| Endgame conversion | Knight vs bad bishop, pawn structure awareness? |
| Bb4 discipline | (vs Nc3) Always Winawer? Aman never deviates. |

---

### Step 3: Report Card

Produce a graded report card:

| Principle | Grade | Notes |
|-----------|-------|-------|
| [relevant principle] | ✅/🟡/❌ + letter | [specific observation with move reference] |

Use only the principles relevant to the detected opening. Don't grade Stonewall criteria on a French game or vice versa.

### Step 4: Verdict

End with "**Single biggest improvement:**" — one actionable takeaway tied to a specific moment in the game.

---

## Mode 2: PDF Maintenance

**Stonewall PDF** ("our SW PDF", "stonewall cheatsheet", "update the stonewall"):
1. Read `skills/openings-coach/references/stonewall-notes.md`
2. Read `chess-db/generate_pdf.py` first
3. Make edits
4. Regenerate: `python3 chess-db/generate_pdf.py`
5. Send updated PDF

**French PDF** ("French PDF", "French cheatsheet", "update the French"):
1. Read `chess-db/tag_french.py` AND `chess-db/generate_french_pdf.py` first
2. Make edits
3. Regenerate: `python3 chess-db/tag_french.py && python3 chess-db/generate_french_pdf.py`
4. Send updated PDF

---

## Mode 3: Pattern Questions

When Dash asks about opening patterns/stats:

1. Use `chess-db/parse_pgn.py` to query the appropriate database
2. For Stonewall, cross-reference with `skills/openings-coach/references/stonewall-notes.md` and the current corpus/generator — not old MEMORY snippets
3. Always link to relevant lichess study games (ChapterURL header)
4. If the question spans both openings, compare them (e.g. "how does Aman handle bad bishops in SW vs French?")

---

## Key Files

| File | Purpose |
|------|---------|
| `chess-db/parse_pgn.py` | PGN parser (MANDATORY — never use regex) |
| `chess-db/games.pgn` | All games (Stonewall + French + Habits) |
| `chess-db/sources.txt` | Lichess study IDs |
| `chess-db/generate_pdf.py` | Stonewall PDF generator |
| `skills/openings-coach/references/stonewall-notes.md` | Stonewall-local insights, migration state, anti-regression notes |
| `chess-db/stonewall-cheatsheet.pdf` | Current Stonewall PDF |
| `chess-db/tag_french.py` | French game tagger |
| `chess-db/generate_french_pdf.py` | French PDF generator |
| `chess-db/french-cheatsheet.pdf` | Current French PDF |
| `chess-db/tag_games.py` | General game tagger (if exists) |

## Critical Rules

- **ALWAYS use parse_pgn.py** — old regex drops 50%+ of Black moves
- **Detect the opening first** — don't assume Stonewall
- **Link games** — every claim should have clickable lichess study links
- **Verify stats** before stating them — run the query, don't guess from memory
- **No hardcoded living-doc stats** — if the DB can change, compute both counts and percentages from current data
- **Keep side-specific notes on the correct side** — don't mirror a White-only timing issue into the Black section without direct support
- **Correct yourself** when wrong — Dash trusts these numbers
- **Cross-reference patterns** — if a French Exchange game tries SW, mention both contexts
