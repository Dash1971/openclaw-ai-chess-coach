---
name: chess-opening-study
description: Extract and annotate high-quality French Defense or Stonewall games from any chess.com player for lichess study import. Triggers when user pastes a chess.com player link AND asks for "French analysis", "French study", "Stonewall analysis", or "Stonewall study". Does NOT trigger on a bare link (that defaults to chess-opponent-scout). Requires explicit opening keyword.
---

# Chess Opening Study Builder

Extract instructive wins from any chess.com player, annotated with Aman Hambleton's speedrun frameworks, ready for lichess study import.

## Trigger

**All of these must be present:**
1. A chess.com player link or username (e.g. `chess.com/member/USERNAME/games`)
2. An explicit opening keyword: "French" or "Stonewall" (or "SW")
3. Intent for study extraction (e.g. "analysis", "study", "games", "extract")

**Examples:**
- "chess.com/member/hikaru/games — French analysis" ✅
- "Give me a French study from Juwen's games" ✅
- "Stonewall analysis for <username>" ✅
- "chess.com/member/hikaru/games" ❌ (no opening keyword → defaults to scout)

## Procedure

### Step 1: Download Games

Extract username from the link. Check if games already exist:
- `opponents/<username>/games.pgn` (from prior scout)
- `<username>/games.pgn` (from prior profile analysis)

If not found, download fresh:
```bash
python3 skills/chess-opponent-scout/scripts/analyze_player.py <username> opponents/<username>
```

### Step 2: Identify Qualifying Games

**For French analysis:**
- Verify opening from actual moves: `1.e4 e6` (as Black) or opponent played `1.e4` and player responded `e6`
- Player must have won (result matches player's color)
- Also include games where player was White against the French (1.e4 e6) — annotate from the opponent's perspective
- Minimum 20 moves (filter out mouse slips)
- Exclude games won purely on time where the position was unclear (judgment call: if total moves < 25 and won on time, flag for review)

**For Stonewall analysis:**
- Detect Stonewall structure: d4+e3+f4+Bd3 (White) or d5+e6+f5 (Black, typically with Bd6)
- Player must have won
- Minimum 20 moves
- Same time-win filter

### Step 3: Classify Variation

**French variations** (from actual moves, not ECO):
- Exchange: White plays exd5 early
- Advanced: White plays e5
- Winawer: Nc3 Bb4
- Tarrasch Open: Nd2 ... exd5 Qxd5
- Tarrasch Closed: Nd2 without early exchange
- Classical: Nc3 Nf6 (often with Bg5)
- KIA/Sideline: White plays d3, Qe2, g3, etc.

**Stonewall sub-types:**
- White Stonewall: d4 e3 f4 Bd3
- Black Stonewall: d5 e6 f5 (vs d4)
- Anti-London Black SW: vs Bf4, early Bd6 challenge

### Step 4: Annotate

Run the annotation script:
```bash
python3 skills/chess-opening-study/scripts/build_study.py <username> <opening> [--max N] [--min-moves M]
```

Arguments:
- `username`: chess.com username
- `opening`: `french` or `stonewall`
- `--max N`: maximum games to include (default: 64)
- `--min-moves M`: minimum game length (default: 20)

**French annotations** (from Aman's sterkurstrakur framework):

*Exchange:*
- Three-plan decision tree: SW attempt → Aggressive O-O-O → Conservative O-O
- LSB activation (Bg4/Bf5/Be6)
- f6 response to Bg5 ("wanted anyway")
- Opponent disruptions: Qe2+, Nc3, c4, Re1+

*Advanced:*
- Chain attack: Qb6 + Nc6 + c5 pressure on d4
- b2 blunder pattern
- Ne7 → f5 break
- Bd7 → Bb5 LSB maneuver

*Winawer:*
- Bb4 discipline (100% after Nc3 in Aman's games)
- Ba6 trade (b6 → Ba6)
- Nxa6 → Nb8 → Nc6 reroute
- h5 counter, Qg4 awareness

*Tarrasch:*
- c5 response to Nd2
- Open vs Closed sub-plans
- IQP compensation in Tarrasch Open

*Classical:*
- Burn variation (dxe4)
- Bg5 handling
- gxf6 bishop pair ideas

*Universal French:*
- Castling choice (KS 60% / QS 17% / never 23%)
- Knight vs bad bishop endgame (15-game theme)
- Pawn structure awareness

**Stonewall annotations** (from Aman's wonestall framework):

*White:*
- Move order: Bd3 timing (move 3 in 61%)
- Ne5 (76%), Nd2 support (82%)
- DSB maneuver attempts
- g4 storm, e4 break, Bxh7+ Greek gift (12%)

*Black:*
- Pawns before pieces (76% play 4+ first)
- Ne4 (81%, avg move 11)
- LSB maneuver (Bd7 → Be8 → Bh5)
- Anti-London: early Bd6 challenge
- Qe8 reroute

### Step 5: Quality Filter

After annotation, review each game:
- Remove games with < 3 thematic annotations (probably not instructive)
- Prioritize games against stronger opponents (sort by opponent Elo desc)
- Cap at `--max` (default 64) games
- Ensure variation mix: don't let one variation dominate more than 40% unless the data dictates it

### Step 6: Output

Write PGN to: `opponents/<username>/<username>-<opening>-study.pgn`

PGN format:
- Clean headers (Event, Site, Date, White, Black, Result, WhiteElo, BlackElo, ECO, Link)
- Event header: `"<Player> <Opening>: <Variation>"`
- Annotations as `{ text }` inline comments
- Proper move numbering (standard PGN, not chess.com format)

### Step 7: Deliver

Send PGN file to Dash via message tool with summary:
- Total games included
- Variation breakdown
- Opponent rating range
- Import instructions: "Studies → Create Study → Import PGN"

### Step 8: Log

Record in `memory/YYYY-MM-DD.md`:
- Player analyzed
- Opening type
- Games found / games included
- Variation breakdown
- Any notable patterns

## Key Files

| File | Purpose |
|------|---------|
| `skills/chess-opening-study/scripts/build_study.py` | Main extraction + annotation script |
| `skills/chess-opponent-scout/scripts/analyze_player.py` | Game downloader (reused) |
| `chess_tools/parse_pgn.py` | PGN parser (MANDATORY) |
| local reference corpus (typically `chess-data-private/corpora/games.pgn`) | Aman/public reference database used for comparison |
| `chess-data-private/generated/stonewall-cheatsheet.pdf` | Optional Stonewall reference in this repo family |
| `chess-data-private/generated/french-cheatsheet.pdf` | Optional French reference in this repo family |

## Critical Rules

- **ALWAYS use parse_pgn.py or equivalent proper parser** — never one-line regex for PGN
- **Verify opening from moves, not ECO codes** — chess.com ECO codes are unreliable
- **Quality > quantity** — 20 well-annotated games beats 64 lightly-annotated ones
- **Sort by opponent Elo** — strongest opposition first (most instructive)
- **Link games** — include chess.com Link header for reference
