# Example commands and prompts

## Study DB sync + search

Update the local study database:

```bash
python3 scripts/update_db.py
```

Search the full staged database:

```bash
python3 scripts/search.py --db data/study-db/games.pgn d4 d5 e3 e6 Bd3
```

## AI coach game analysis

Typical prompt:

> Analyze this game against the Stonewall corpus and tell me the single biggest mistake in the opening plan.

Typical prompt:

> Analyze this game against the French corpus and grade the opening decisions.

## Opponent report

Download a chess.com player:

```bash
python3 scripts/analyze_player.py <username> tmp/<username> --platform chesscom
```

Typical prompt:

> Build a scouting report for this opponent and summarize the biggest exploitable opening patterns.

## Opening cheat sheets

Stonewall:

```bash
python3 scripts/tag_games.py
python3 scripts/generate_stonewall_pdf.py
```

French:

```bash
python3 scripts/tag_french.py
python3 scripts/generate_french_pdf.py
```
