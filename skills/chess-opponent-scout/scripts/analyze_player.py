#!/usr/bin/env python3
"""
Chess Player Analysis Engine — supports chess.com AND lichess.
Auto-detects platform from --platform flag or defaults to chess.com.
Usage:
  python3 analyze_player.py <username> <output_dir> [--platform chesscom|lichess]

For lichess: downloads standard games only (excludes "From Position" variant).
"""

import re, json, sys, os, time, urllib.request
from collections import Counter, defaultdict

ECO_FAMILIES = {
    'A00-A09': 'Irregular/Flank', 'A10-A39': 'English Opening',
    'A40-A44': "Queen's Pawn (misc)", 'A45-A49': 'Indian/Trompowsky',
    'A50-A79': 'Indian Systems', 'A80-A99': 'Dutch Defense',
    'B00-B09': 'Misc 1.e4', 'B10-B19': 'Caro-Kann', 'B20-B99': 'Sicilian',
    'C00-C19': 'French', 'C20-C29': "King's Pawn (open)",
    'C30-C39': "King's Gambit", 'C40-C49': 'Open Games (Philidor/Scotch/4Kts)',
    'C50-C59': 'Italian/Giuoco Piano', 'C60-C99': 'Ruy Lopez',
    'D00-D05': "Queen's Pawn (misc d)", 'D06-D09': 'QGD (misc)',
    'D10-D19': 'Slav', 'D20-D29': 'QGA', 'D30-D69': 'QGD',
    'D70-D99': 'Grünfeld', 'E00-E09': 'Catalan', 'E10-E19': "Queen's Indian",
    'E20-E59': 'Nimzo-Indian', 'E60-E99': "King's Indian",
}

def eco_to_family(eco):
    if not eco or eco in ('unknown', '?'): return 'Unknown'
    letter = eco[0]
    try: num = int(eco[1:])
    except: return 'Unknown'
    for r, name in ECO_FAMILIES.items():
        parts = r.split('-')
        sl, sn = parts[0][0], int(parts[0][1:])
        el, en = parts[1][0], int(parts[1][1:])
        if letter == sl and sn <= num <= en: return name
    return f'{letter}-other'


# ── Downloads ────────────────────────────────────────────────────────────

def download_chesscom(username, output_dir):
    """Download all games from chess.com API. Returns pgn_path."""
    os.makedirs(output_dir, exist_ok=True)
    pgn_path = os.path.join(output_dir, 'games.pgn')
    meta_path = os.path.join(output_dir, 'games_meta.json')

    url = f"https://api.chess.com/pub/player/{username}/games/archives"
    req = urllib.request.Request(url, headers={"User-Agent": "OpenClaw/1.0"})
    with urllib.request.urlopen(req) as resp:
        archives = json.loads(resp.read())["archives"]

    print(f"Found {len(archives)} monthly archives for {username}")
    all_pgn, all_meta = [], []

    for i, aurl in enumerate(archives):
        try:
            req = urllib.request.Request(aurl, headers={"User-Agent": "OpenClaw/1.0"})
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
            games = data.get("games", [])
            for g in games:
                if "pgn" in g: all_pgn.append(g["pgn"])
                all_meta.append({k: v for k, v in g.items() if k != "pgn"})
            month = aurl.split('/')[-2] + '/' + aurl.split('/')[-1]
            print(f"  [{i+1}/{len(archives)}] {month}: {len(games)} games")
            time.sleep(0.3)
        except Exception as e:
            print(f"  [{i+1}/{len(archives)}] ERROR: {e}")

    with open(pgn_path, 'w') as f:
        f.write("\n\n".join(all_pgn))
    with open(meta_path, 'w') as f:
        json.dump(all_meta, f)
    print(f"Downloaded {len(all_pgn)} games from chess.com")
    return pgn_path


def download_lichess(username, output_dir):
    """Download standard games from lichess API (excludes From Position). Returns pgn_path."""
    os.makedirs(output_dir, exist_ok=True)
    raw_path = os.path.join(output_dir, 'games_raw.pgn')
    pgn_path = os.path.join(output_dir, 'games.pgn')

    # Download all perf types (standard variant games)
    url = f"https://lichess.org/api/games/user/{username}?perfType=bullet,blitz,rapid,classical,correspondence&opening=true"
    req = urllib.request.Request(url, headers={
        "Accept": "application/x-chess-pgn",
        "User-Agent": "OpenClaw/1.0"
    })
    print(f"Downloading lichess games for {username}...")
    with urllib.request.urlopen(req) as resp:
        data = resp.read().decode('utf-8')
    with open(raw_path, 'w') as f:
        f.write(data)

    # Filter out "From Position" games
    raw_games = re.split(r'\n\n(?=\[Event )', data.strip())
    standard = [g for g in raw_games if '[Variant "From Position"]' not in g and g.strip()]
    from_pos_count = len(raw_games) - len(standard)

    with open(pgn_path, 'w') as f:
        f.write('\n\n'.join(standard))
    print(f"Downloaded {len(raw_games)} total, filtered to {len(standard)} standard games ({from_pos_count} From Position excluded)")
    return pgn_path


def get_player_info_chesscom(username):
    try:
        url = f"https://api.chess.com/pub/player/{username}"
        req = urllib.request.Request(url, headers={"User-Agent": "OpenClaw/1.0"})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except:
        return {}


def get_player_info_lichess(username):
    try:
        url = f"https://lichess.org/api/user/{username}"
        req = urllib.request.Request(url, headers={"User-Agent": "OpenClaw/1.0"})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except:
        return {}


# ── PGN Parsing ──────────────────────────────────────────────────────────

def parse_pgn(path):
    games = []
    with open(path) as f:
        content = f.read()
    for raw in re.split(r'\n\n(?=\[Event )', content.strip()):
        if not raw.strip(): continue
        g = {}
        for k, v in re.findall(r'\[(\w+)\s+"([^"]*)"\]', raw):
            g[k] = v
        lines = raw.strip().split('\n')
        ml = [l.strip() for l in lines if not l.startswith('[') and l.strip()]
        g['moves_raw'] = ' '.join(ml)
        clean = re.sub(r'\{[^}]*\}', '', g['moves_raw'])
        clean = re.sub(r'\([^)]*\)', '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        moves = []
        for t in clean.split():
            if t in ['1-0', '0-1', '1/2-1/2', '*']: continue
            if re.match(r'^\d+\.+$', t): continue
            if re.match(r'^[A-Za-z]', t) or t in ['O-O', 'O-O-O']:
                moves.append(t)
        g['moves'] = moves
        g['num_moves'] = len(moves)
        games.append(g)
    return games


# ── Analysis ─────────────────────────────────────────────────────────────

def analyze(games, username, platform='chesscom'):
    """Run full analysis. Returns stats dict."""
    uname = username.lower()

    def is_white(g): return g.get('White', '').lower() == uname
    def res(g):
        r = g.get('Result', '*')
        w = is_white(g)
        if r == '1-0': return 'win' if w else 'loss'
        if r == '0-1': return 'loss' if w else 'win'
        if r == '1/2-1/2': return 'draw'
        return 'unknown'
    def month(g):
        d = g.get('Date', g.get('UTCDate', ''))
        if not d or len(d) < 7: return None
        return d[:7].replace('.', '-')
    def elo(g):
        e = g.get('WhiteElo' if is_white(g) else 'BlackElo', '')
        return int(e) if e and e not in ('?', '-') and e.isdigit() else None
    def opp_elo(g):
        e = g.get('BlackElo' if is_white(g) else 'WhiteElo', '')
        return int(e) if e and e not in ('?', '-') and e.isdigit() else None

    def tc(g):
        if platform == 'lichess':
            event = g.get('Event', '').lower()
            if 'correspondence' in event: return 'correspondence'
        tc_val = g.get('TimeControl', '')
        if not tc_val or tc_val == '-':
            if platform == 'lichess':
                event = g.get('Event', '').lower()
                for t in ['bullet', 'blitz', 'rapid', 'classical']:
                    if t in event: return t
            return 'unknown'
        if '/' in tc_val:
            return 'daily' if platform == 'chesscom' else 'correspondence'
        parts = tc_val.split('+')
        try: base = int(parts[0])
        except: return 'unknown'
        inc = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        total = base + 40 * inc
        if total < 180: return 'bullet'
        elif total < 600: return 'blitz'
        elif total < 1800: return 'rapid'
        else: return 'classical'

    def is_rated(g):
        if platform == 'lichess':
            return 'rated' in g.get('Event', '').lower()
        return True  # chess.com games are all rated

    def castling(moves, color):
        for i, m in enumerate(moves):
            if color == 'white' and i % 2 == 0:
                if m == 'O-O': return 'kingside'
                if m == 'O-O-O': return 'queenside'
            elif color == 'black' and i % 2 == 1:
                if m == 'O-O': return 'kingside'
                if m == 'O-O-O': return 'queenside'
        return 'none'

    def castle_move_num(moves, color):
        count = 0
        for i, m in enumerate(moves):
            if color == 'white' and i % 2 == 0:
                count += 1
                if m in ['O-O', 'O-O-O']: return count
            elif color == 'black' and i % 2 == 1:
                count += 1
                if m in ['O-O', 'O-O-O']: return count
        return None

    wg = [g for g in games if is_white(g)]
    bg = [g for g in games if not is_white(g)]
    s = {}

    # Basic
    r_all = Counter(res(g) for g in games)
    r_w = Counter(res(g) for g in wg)
    r_b = Counter(res(g) for g in bg)
    s['total'] = len(games)
    s['as_white'] = len(wg)
    s['as_black'] = len(bg)
    s['results'] = dict(r_all)
    s['white_results'] = dict(r_w)
    s['black_results'] = dict(r_b)
    s['win_rate'] = r_all['win'] / len(games) * 100 if games else 0
    s['score_rate'] = (r_all['win'] + 0.5 * r_all['draw']) / len(games) * 100 if games else 0
    s['white_win_rate'] = r_w['win'] / len(wg) * 100 if wg else 0
    s['black_win_rate'] = r_b['win'] / len(bg) * 100 if bg else 0
    s['draw_rate'] = r_all['draw'] / len(games) * 100 if games else 0

    # Platform-specific: rated/casual and bot detection (lichess)
    if platform == 'lichess':
        rated_games = [g for g in games if is_rated(g)]
        casual_games = [g for g in games if not is_rated(g)]
        s['rated_count'] = len(rated_games)
        s['casual_count'] = len(casual_games)
        for label, gset in [('rated_performance', rated_games), ('casual_performance', casual_games)]:
            if gset:
                r = Counter(res(g) for g in gset)
                total = len(gset)
                s[label] = {'games': total, 'win': r['win'], 'draw': r['draw'], 'loss': r['loss'],
                            'score': (r['win'] + 0.5 * r['draw']) / total * 100}

        bot_games = [g for g in games if 'BOT' in g.get('WhiteTitle', '') or 'BOT' in g.get('BlackTitle', '')]
        human_games = [g for g in games if g not in bot_games]
        for label, gset in [('vs_bots', bot_games), ('vs_humans', human_games)]:
            if gset:
                r = Counter(res(g) for g in gset)
                total = len(gset)
                s[label] = {'games': total, 'win': r['win'], 'draw': r['draw'], 'loss': r['loss'],
                            'score': (r['win'] + 0.5 * r['draw']) / total * 100}

    # Time controls
    tc_d = Counter(tc(g) for g in games)
    s['time_controls'] = dict(tc_d)
    s['tc_performance'] = {}
    tc_types = ['bullet', 'blitz', 'rapid', 'classical', 'correspondence'] if platform == 'lichess' else ['bullet', 'blitz', 'rapid', 'classical', 'daily']
    for t in tc_types:
        tg = [g for g in games if tc(g) == t]
        if tg:
            r = Counter(res(g) for g in tg)
            total = len(tg)
            s['tc_performance'][t] = {
                'games': total, 'win': r['win'], 'draw': r['draw'], 'loss': r['loss'],
                'score': (r['win'] + 0.5 * r['draw']) / total * 100
            }

    # Elo by month
    em = defaultdict(list)
    for g in games:
        m, e = month(g), elo(g)
        if m and e: em[m].append(e)
    s['elo_by_month'] = {m: {'avg': sum(v) // len(v), 'min': min(v), 'max': max(v), 'games': len(v)}
                         for m, v in sorted(em.items())}

    # First moves (White)
    fm = Counter(g['moves'][0] for g in wg if g['moves'])
    s['first_move_white'] = [(m, c) for m, c in fm.most_common(10)]
    fm_results = {}
    for m, c in fm.most_common(5):
        gs = [g for g in wg if g['moves'] and g['moves'][0] == m]
        r = Counter(res(g) for g in gs)
        fm_results[m] = {'games': c, 'win_pct': r['win'] / c * 100, 'score': (r['win'] + 0.5 * r['draw']) / c * 100}
    s['first_move_results'] = fm_results

    # First move evolution
    fm_evo = defaultdict(lambda: Counter())
    for g in wg:
        m = month(g)
        if m and g['moves']:
            fm_evo[m][g['moves'][0]] += 1
    s['first_move_evolution'] = {m: dict(c.most_common(5)) for m, c in sorted(fm_evo.items())}

    # Response to e4/d4
    e4r = Counter()
    d4r = Counter()
    for g in bg:
        if g['moves'] and len(g['moves']) >= 2:
            if g['moves'][0] == 'e4': e4r[g['moves'][1]] += 1
            elif g['moves'][0] == 'd4': d4r[g['moves'][1]] += 1
    s['response_to_e4'] = [(r, c) for r, c in e4r.most_common(10)]
    s['response_to_d4'] = [(r, c) for r, c in d4r.most_common(10)]

    # ECO families
    for label, gset in [('eco_white', wg), ('eco_black', bg)]:
        ef = defaultdict(lambda: Counter())
        efc = Counter()
        for g in gset:
            f = eco_to_family(g.get('ECO', ''))
            efc[f] += 1
            ef[f][res(g)] += 1
        s[label] = {}
        for f, c in efc.most_common(25):
            r = ef[f]
            total = sum(r.values())
            s[label][f] = {
                'games': total, 'win': r['win'], 'draw': r['draw'], 'loss': r['loss'],
                'score': (r['win'] + 0.5 * r['draw']) / total * 100 if total else 0
            }

    # Lichess opening names (lichess provides Opening header)
    if platform == 'lichess':
        opening_counter = Counter()
        opening_results = defaultdict(lambda: Counter())
        for g in games:
            op = g.get('Opening', '?')
            if op and op != '?':
                base = op.split(':')[0].strip()
                opening_counter[base] += 1
                opening_results[base][res(g)] += 1
        s['top_openings'] = []
        for op, c in opening_counter.most_common(20):
            r = opening_results[op]
            total = sum(r.values())
            s['top_openings'].append({
                'name': op, 'games': c,
                'win': r['win'], 'draw': r['draw'], 'loss': r['loss'],
                'score': (r['win'] + 0.5 * r['draw']) / total * 100 if total else 0
            })

    # Castling
    cw = Counter(castling(g['moves'], 'white') for g in wg)
    cb = Counter(castling(g['moves'], 'black') for g in bg)
    s['castling_white'] = dict(cw)
    s['castling_black'] = dict(cb)
    ctw = [castle_move_num(g['moves'], 'white') for g in wg]
    ctb = [castle_move_num(g['moves'], 'black') for g in bg]
    ctw = [x for x in ctw if x]
    ctb = [x for x in ctb if x]
    s['castle_timing_white'] = sum(ctw) / len(ctw) if ctw else 0
    s['castle_timing_black'] = sum(ctb) / len(ctb) if ctb else 0

    # Opposite side castling
    osc_games = []
    for g in games:
        if is_white(g):
            jc = castling(g['moves'], 'white')
            oc = castling(g['moves'], 'black')
        else:
            jc = castling(g['moves'], 'black')
            oc = castling(g['moves'], 'white')
        if jc != 'none' and oc != 'none' and jc != oc:
            osc_games.append(g)
    osc_r = Counter(res(g) for g in osc_games)
    s['osc_count'] = len(osc_games)
    s['osc_pct'] = len(osc_games) / len(games) * 100 if games else 0
    s['osc_results'] = dict(osc_r)

    # Game length
    lengths = [g['num_moves'] // 2 for g in games]
    s['avg_length'] = sum(lengths) / len(lengths) if lengths else 0
    s['median_length'] = sorted(lengths)[len(lengths) // 2] if lengths else 0
    wl = [g['num_moves'] // 2 for g in games if res(g) == 'win']
    ll = [g['num_moves'] // 2 for g in games if res(g) == 'loss']
    s['avg_length_wins'] = sum(wl) / len(wl) if wl else 0
    s['avg_length_losses'] = sum(ll) / len(ll) if ll else 0

    eg = sum(1 for g in games if g['num_moves'] > 80)
    s['endgame_pct'] = eg / len(games) * 100 if games else 0
    qw = sum(1 for g in games if res(g) == 'win' and g['num_moves'] // 2 <= 25)
    mw = sum(1 for g in games if res(g) == 'win' and g['num_moves'] // 2 >= 60)
    s['quick_wins'] = qw
    s['marathon_wins'] = mw

    # Terminations
    win_term = Counter()
    loss_term = Counter()
    for g in games:
        t = g.get('Termination', '').lower()
        cat = 'other'
        if 'checkmate' in t or 'mate' in t: cat = 'checkmate'
        elif 'resign' in t: cat = 'resignation'
        elif 'time' in t: cat = 'time'
        r = res(g)
        if r == 'win': win_term[cat] += 1
        elif r == 'loss': loss_term[cat] += 1
    s['win_by'] = dict(win_term)
    s['loss_by'] = dict(loss_term)

    # Style metrics
    checks_given = checks_received = 0
    for g in games:
        color = 'white' if is_white(g) else 'black'
        for i, m in enumerate(g['moves']):
            if '+' in m or '#' in m:
                if (color == 'white' and i % 2 == 0) or (color == 'black' and i % 2 == 1):
                    checks_given += 1
                else:
                    checks_received += 1
    s['checks_given_per_game'] = checks_given / len(games) if games else 0
    s['checks_received_per_game'] = checks_received / len(games) if games else 0

    captures = [g['moves_raw'].count('x') for g in games]
    s['avg_captures'] = sum(captures) / len(captures) if captures else 0

    eq_w = sum(1 for g in wg if any(g['moves'][i].rstrip('+#').startswith('Q')
               for i in range(0, min(10, len(g['moves'])), 2) if i < len(g['moves'])))
    eq_b = sum(1 for g in bg if any(g['moves'][i].rstrip('+#').startswith('Q')
               for i in range(1, min(11, len(g['moves'])), 2) if i < len(g['moves'])))
    s['early_queen_white'] = eq_w / len(wg) * 100 if wg else 0
    s['early_queen_black'] = eq_b / len(bg) * 100 if bg else 0

    # Pawn storms
    ks_w = sum(1 for g in wg if sum(1 for i, m in enumerate(g['moves']) if i % 2 == 0 and m.rstrip('+#') in ['g4', 'h4', 'f4', 'g5', 'h5']) >= 2)
    qs_w = sum(1 for g in wg if sum(1 for i, m in enumerate(g['moves']) if i % 2 == 0 and m.rstrip('+#') in ['a4', 'b4', 'c4', 'a5', 'b5']) >= 2)
    ks_b = sum(1 for g in bg if sum(1 for i, m in enumerate(g['moves']) if i % 2 == 1 and m.rstrip('+#') in ['g5', 'h5', 'f5', 'g4', 'h4']) >= 2)
    qs_b = sum(1 for g in bg if sum(1 for i, m in enumerate(g['moves']) if i % 2 == 1 and m.rstrip('+#') in ['a5', 'b5', 'c5', 'a4', 'b4']) >= 2)
    s['pawn_storms'] = {'ks_white': ks_w, 'qs_white': qs_w, 'ks_black': ks_b, 'qs_black': qs_b}

    # Opening sequences (white, first 3 own moves)
    oseq = Counter()
    for g in wg:
        wm = [g['moves'][i] for i in range(0, min(6, len(g['moves'])), 2)]
        if len(wm) >= 3:
            oseq[' '.join(wm[:3])] += 1
    s['opening_sequences'] = [(seq, c) for seq, c in oseq.most_common(15)]

    # Monthly performance
    mp = defaultdict(lambda: Counter())
    for g in games:
        m = month(g)
        if m: mp[m][res(g)] += 1
    s['monthly_performance'] = {}
    for m in sorted(mp.keys()):
        r = mp[m]
        total = sum(r.values())
        s['monthly_performance'][m] = {
            'games': total, 'win': r['win'], 'draw': r['draw'], 'loss': r['loss'],
            'score': (r['win'] + 0.5 * r['draw']) / total * 100 if total else 0
        }

    # Rating bands
    s['vs_rating_bands'] = {}
    for name, lo, hi in [('<600', 0, 600), ('600-799', 600, 800), ('800-999', 800, 1000),
                          ('1000-1199', 1000, 1200), ('1200-1399', 1200, 1400), ('1400-1599', 1400, 1600),
                          ('1600-1799', 1600, 1800), ('1800-1999', 1800, 2000), ('2000-2199', 2000, 2200),
                          ('2200-2399', 2200, 2400), ('2400-2599', 2400, 2600), ('2600+', 2600, 9999)]:
        bg2 = [g for g in games if opp_elo(g) and lo <= opp_elo(g) < hi]
        if bg2:
            r = Counter(res(g) for g in bg2)
            total = len(bg2)
            s['vs_rating_bands'][name] = {
                'games': total, 'win': r['win'], 'draw': r['draw'], 'loss': r['loss'],
                'score': (r['win'] + 0.5 * r['draw']) / total * 100
            }

    # Top opponents
    opp_c = Counter()
    opp_r = defaultdict(lambda: Counter())
    for g in games:
        o = g.get('Black' if is_white(g) else 'White', '')
        opp_c[o] += 1
        opp_r[o][res(g)] += 1
    s['top_opponents'] = [{'name': o, 'games': c, **dict(opp_r[o])} for o, c in opp_c.most_common(15)]

    return s


# ── Main ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    args = sys.argv[1:]
    platform = 'chesscom'

    # Parse --platform flag
    if '--platform' in args:
        idx = args.index('--platform')
        platform = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if len(args) < 2:
        print("Usage: python3 analyze_player.py <username> <output_dir> [--platform chesscom|lichess]")
        sys.exit(1)

    username = args[0]
    output_dir = args[1]

    if platform == 'lichess':
        info = get_player_info_lichess(username)
        pgn_path = download_lichess(username, output_dir)
    else:
        info = get_player_info_chesscom(username)
        pgn_path = download_chesscom(username, output_dir)

    games = parse_pgn(pgn_path)
    stats = analyze(games, username, platform)
    stats['username'] = username
    stats['platform'] = platform
    stats['profile'] = info

    out_name = 'lichess_analysis.json' if platform == 'lichess' else 'analysis.json'
    out_path = os.path.join(output_dir, out_name)
    with open(out_path, 'w') as f:
        json.dump(stats, f, indent=2, default=str)

    # Backward-compatible convenience copy for callers that expect analysis.json
    if platform == 'lichess':
        with open(os.path.join(output_dir, 'analysis.json'), 'w') as f:
            json.dump(stats, f, indent=2, default=str)

    print(f"\nAnalysis complete: {stats['total']} games → {out_path}")
