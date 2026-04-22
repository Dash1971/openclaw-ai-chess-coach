---
name: chess-opponent-scout
description: Generate a scouting report for any chess.com or Lichess account based on public games, repertoire, time controls, style, and vulnerabilities. This is the default skill when a player link is provided without an opening-specific study request.
---

# Chess Opponent Scout

Generate a scouting report for a public chess account.

## Platform detection

- `chess.com/member/USERNAME` or `.../games` -> chess.com
- `lichess.org/@/USERNAME` -> Lichess
- bare username + "scout" -> ask which platform if unclear

## Procedure

1. detect the platform and extract the username
2. run:

```bash
python3 skills/chess-opponent-scout/scripts/analyze_player.py <username> scouting/<username> --platform <chesscom|lichess>
```

3. read the generated `analysis.json` and supporting files
4. produce a report covering:
   - repertoire
   - format and time-control profile
   - style tendencies
   - strengths
   - vulnerabilities
   - practical preparation advice

## Output structure

Recommended sections:
1. account summary
2. white repertoire
3. black repertoire
4. format/time-control profile
5. style profile
6. strengths
7. vulnerabilities
8. practical preparation plan

## Comparison mode

If the user explicitly asks for account-vs-account comparison, analyze both accounts and compare them neutrally.

Do not rely on privileged identity mappings or a built-in “self” profile. The workflow should remain username-driven.

## Lichess notes

- Lichess opening headers are often useful for human-readable summaries
- separate rated and casual games when the split matters
- note bot-game share when it is material
- when comparing chess.com and Lichess accounts, mention rating-pool differences

## Practical advice rule

- for opponent prep: show how to exploit weaknesses
- for self-scouting: turn the same data into self-improvement advice
- for correspondence/daily play: emphasize positional and opening preparation over clock pressure
