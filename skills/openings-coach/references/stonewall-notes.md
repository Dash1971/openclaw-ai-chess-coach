# Stonewall Notes (Local Reference)

Use this file for Stonewall-specific insights, migration state, and PDF anti-regression notes.
Do **not** put these in `MEMORY.md` unless they become genuinely cross-project/global.

## Current Stonewall Study Set

Active Lichess study IDs after the 2026-04-13 migration:
- `zOv1VXUQ`
- `Tk9U1pMu`
- `nD4ZRU2M`
- `xlWBIbwW`

Retired old IDs:
- `jjmB1AcS`
- `bvfOTAKi`
- `48Zommif`

## Current Corpus Snapshot

After the 2026-04-13 refresh:
- White Stonewall games: **116**
- Black Stonewall games: **101**

This matters because the black-side sections now rest on a much thicker sample than before, especially:
- `...Ne4`
- queen reroutes (`...Qe8` / `...Qe7`)
- `...g5`
- LSB maneuver themes

## Stonewall Insights Worth Reusing

### White
- Early `f4` is often prophylaxis against `...Bg4`, keeping `Nf3` available.
- Queen placements like `Qc2` / `Qe1` / `Qe2` often do double duty:
  - protect the light-squared bishop
  - help hold / control `e4`
  - support the right timing of `Nd2` / `Nf3`
- In some symmetrical structures, early `Nd2` is not urgent because Black still contests `e4`; Aman often prefers `Ne5` first.

### Black
- `...Nd7` to stop `Ne5` is situational, not automatic.
- Later / stronger black examples lean more toward:
  - castling
  - bishop activity
  - direct `...Ne4` plans
- Do not force `...Nd7` if it creates structural awkwardness or kills useful c-pawn flexibility.

### Attack Motif
- Exchange sacs on `f3` / `Nxf3`-type attacks recur when:
  - the h-file is live
  - both bishops are cutting toward the king

## PDF Anti-Regression Rules

### 1) No hardcoded counts or percentages in living corpus prose
If a stat can change after a DB refresh, compute it from current data.
Do not mix live counts with stale literal labels or percentages in narrative text.

Bad patterns:
- `38 of 101 games (52%)`
- `vs 1.d4 (18 games)` when the current tagged corpus says 34

Good pattern:
- compute both numerator and percentage from the same current tag set
- derive section labels (opening counts, subgroup counts) from current tags rather than fixed prose

### 2) Keep side-specific ideas on the correct side
Do not mirror a White-only concern into the Black section just because the structure feels analogous.
If a concept is primarily a White timing problem, keep it in the White discussion unless the Black analogue is independently supported by notes/games.

Bad pattern:
- placing the White-side `...Nf6` / `...e5` timing concern under the Black section without direct Black-side support

### 3) Prefer local references over MEMORY.md
For Stonewall PDF updates or Stonewall questions:
- load this file
- load the current generator / tagger
- verify against current corpus

Do not rely on old MEMORY snippets for Stonewall-specific stats.
