#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

USER_AGENT = 'OpenClaw/1.0'
CHUNK_SIZE = 64


@dataclass
class Game:
    index: int
    date: str
    white: str
    black: str
    white_elo: int | None
    black_elo: int | None
    time_control: str
    url: str
    pgn: str
    opponent: str
    as_white: bool
    my_elo: int | None
    opp_elo: int | None


TC_RE = re.compile(r'^(\d+)(?:\+(\d+))?$')
URL_USER_RE = re.compile(r'/member/([^/]+)/game/|/live/game/|/game/live/')


def req_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def normalize_tc(raw: str | None) -> str:
    if not raw:
        return 'unknown'
    if '/' in raw:
        raw = raw.split('/')[-1]
    m = TC_RE.match(raw)
    if not m:
        return raw
    base = int(m.group(1))
    inc = int(m.group(2) or 0)
    mins = base / 60
    if mins.is_integer():
        return f'{int(mins)}+{inc}'
    return f'{mins:g}+{inc}'


def pgn_header(pgn: str, key: str) -> str | None:
    m = re.search(rf'^\[{re.escape(key)} "(.*)"\]$', pgn, re.M)
    return m.group(1) if m else None


def fetch_games(player: str) -> list[Game]:
    archives_url = f'https://api.chess.com/pub/player/{player}/games/archives'
    archives = req_json(archives_url).get('archives', [])
    games: list[Game] = []
    player_lower = player.lower()
    for archive_url in archives:
        data = req_json(archive_url)
        for raw in data.get('games', []):
            pgn = (raw.get('pgn') or '').strip()
            if not pgn:
                continue
            white = ((raw.get('white') or {}).get('username') or pgn_header(pgn, 'White') or '').strip()
            black = ((raw.get('black') or {}).get('username') or pgn_header(pgn, 'Black') or '').strip()
            white_elo = (raw.get('white') or {}).get('rating')
            black_elo = (raw.get('black') or {}).get('rating')
            as_white = white.lower() == player_lower
            opponent = black if as_white else white
            my_elo = white_elo if as_white else black_elo
            opp_elo = black_elo if as_white else white_elo
            games.append(Game(
                index=0,
                date=raw.get('end_time') or pgn_header(pgn, 'Date') or '',
                white=white,
                black=black,
                white_elo=white_elo,
                black_elo=black_elo,
                time_control=normalize_tc(raw.get('time_control') or pgn_header(pgn, 'TimeControl')),
                url=raw.get('url') or '',
                pgn=pgn,
                opponent=opponent,
                as_white=as_white,
                my_elo=my_elo,
                opp_elo=opp_elo,
            ))
    games.sort(key=lambda g: (str(g.date), g.url))
    for i, g in enumerate(games, start=1):
        g.index = i
    return games


def summarize(games: list[Game]) -> dict[str, Any]:
    tc_counts: dict[str, int] = {}
    rating_resets = []
    for i, g in enumerate(games):
        tc_counts[g.time_control] = tc_counts.get(g.time_control, 0) + 1
        if i > 0:
            prev = games[i - 1]
            if g.my_elo is not None and prev.my_elo is not None and prev.my_elo - g.my_elo >= 300:
                rating_resets.append({
                    'index': g.index,
                    'opponent': g.opponent,
                    'my_elo': g.my_elo,
                    'previous_elo': prev.my_elo,
                    'time_control': g.time_control,
                    'url': g.url,
                })
    return {
        'total_games': len(games),
        'time_controls': tc_counts,
        'rating_reset_candidates': rating_resets,
        'first_game': brief(games[0]) if games else None,
        'last_game': brief(games[-1]) if games else None,
        'first_20': [brief(g) for g in games[:20]],
        'last_20': [brief(g) for g in games[-20:]],
    }


def brief(g: Game) -> dict[str, Any]:
    return {
        'index': g.index,
        'date': g.date,
        'opponent': g.opponent,
        'my_elo': g.my_elo,
        'opp_elo': g.opp_elo,
        'time_control': g.time_control,
        'as_white': g.as_white,
        'url': g.url,
    }


def filter_games(games: list[Game], start_index: int | None, end_index: int | None, tc: str | None) -> list[Game]:
    result = games
    if start_index is not None:
        result = [g for g in result if g.index >= start_index]
    if end_index is not None:
        result = [g for g in result if g.index <= end_index]
    if tc is not None:
        result = [g for g in result if g.time_control == tc]
    return result


def write_chunks(games: list[Game], out_dir: Path, prefix: str, chunk_size: int) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(0, len(games), chunk_size):
        chunk = games[i:i + chunk_size]
        num = (i // chunk_size) + 1
        path = out_dir / f'{prefix}_part{num}.pgn'
        path.write_text('\n\n'.join(g.pgn for g in chunk) + '\n', encoding='utf-8')
        paths.append(path)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description='Fetch and extract chess.com speedrun PGNs for a player.')
    sub = ap.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('summary', help='Fetch all games and print a summary to help choose boundaries.')
    s.add_argument('player')
    s.add_argument('--json-out', help='Optional path to save summary JSON.')

    e = sub.add_parser('extract', help='Extract filtered games into chunked PGN files.')
    e.add_argument('player')
    e.add_argument('--start-index', type=int)
    e.add_argument('--end-index', type=int)
    e.add_argument('--time-control', help='Normalized time control like 5+0, 3+0, 15+10')
    e.add_argument('--chunk-size', type=int, default=CHUNK_SIZE)
    e.add_argument('--out-dir', required=True)
    e.add_argument('--prefix')

    args = ap.parse_args()
    games = fetch_games(args.player)

    if args.cmd == 'summary':
        payload = summarize(games)
        text = json.dumps(payload, indent=2)
        print(text)
        if args.json_out:
            Path(args.json_out).write_text(text, encoding='utf-8')
        return 0

    filtered = filter_games(games, args.start_index, args.end_index, args.time_control)
    if not filtered:
        print('No games matched the requested filters.', file=sys.stderr)
        return 1
    prefix = args.prefix or args.player
    paths = write_chunks(filtered, Path(args.out_dir), prefix, args.chunk_size)
    print(json.dumps({
        'player': args.player,
        'selected_games': len(filtered),
        'time_control': args.time_control,
        'start_index': args.start_index,
        'end_index': args.end_index,
        'chunk_size': args.chunk_size,
        'files': [str(p) for p in paths],
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
