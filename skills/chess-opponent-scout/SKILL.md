---
name: chess-opponent-scout
description: Generate a chess intelligence scouting report for any chess.com or lichess player based on that account's public games, repertoire, time-control performance, style, and vulnerabilities. Triggers when the user drops a chess.com or lichess profile link (e.g. chess.com/member/username, lichess.org/@/username), or says "scout [username]", "analyze [username]", or "prepare for [username]". This is the DEFAULT when a chess.com or lichess link is pasted without an opening keyword. Use it for any account, including self-scouting by username, without assuming a built-in identity mapping. NOT for opening-specific study extraction (use chess-opening-study when the user says "French analysis" or "Stonewall analysis").
---

# chess-opponent-scout

Generate a scouting report for a chess account from public games.

## Platform Detection

- `chess.com/member/USERNAME` or `chess.com/member/USERNAME/games` → chess.com (`--platform chesscom`)
- `lichess.org/@/USERNAME` or `lichess.org/api/games/user/USERNAME` → lichess (`--platform lichess`)
- Bare username with "scout" → ask which platform, or default to chess.com

## Data

- **Output dir:** `scouting/<username>/`
- Treat every target account the same way, including self-scouting.
- Do not rely on a built-in Dash profile, combined profile JSON, or any privileged identity mapping.

## Procedure

1. Extract username and detect platform from the link.
2. Run `python3 scripts/analyze_player.py <username> <workspace>/scouting/<username> --platform <chesscom|lichess>`.
   - For lichess: automatically excludes "From Position" variant games — only standard games included.
3. Read the generated `analysis.json` and supporting files.
4. Generate a scouting report focused on:
   - repertoire
   - time-control performance
   - style and game length patterns
   - strengths
   - vulnerabilities
   - practical preparation advice
5. If the user explicitly asks for a comparison against another account, analyze both accounts and compare them neutrally. Do not assume any default baseline account.
6. Deliver the report in the active chat and log the work in `memory/YYYY-MM-DD.md` if it is significant.

## Lichess-Specific Notes

- Lichess provides `[Opening "..."]` headers — use these for human-readable opening names.
- Lichess has rated + casual games; report both separately when significant.
- Lichess has bot opponents (Maia, Stockfish) — flag bot-game share if >10%.
- Rating systems differ: lichess ratings are typically higher than chess.com for the same skill level.
- When comparing accounts across platforms, note the rating-pool difference explicitly.

## Report Structure

### Core sections
1. account summary
2. white repertoire
3. black repertoire
4. format/time-control profile
5. style profile
6. strengths
7. vulnerabilities
8. practical preparation plan

### Optional comparison section
Include only when the user explicitly asks for account-vs-account comparison.

Comparison ideas:
- win rate / draw rate
- average game length / endgame rate
- checkmate win % / time-loss %
- best format
- castling rate
- primary white/black openings
- quick-win rate

### Practical advice
- If the target is being scouted as an opponent, give concrete ways to exploit weaknesses.
- If the target is being self-scouted, give concrete self-improvement advice instead of pretending they are a separate opponent.
- For daily/correspondence play, emphasize positional preparation and opening choices over clock pressure.

## Output rule

Keep the workflow generic and username-driven. The skill should work the same way for any chess.com or lichess account, including Dash's own accounts, without storing a special self-profile reference file.
