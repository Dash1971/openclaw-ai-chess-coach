#!/usr/bin/env python3
"""
Tag sterkurstrakur French Defense games with thematic categories.
Outputs /tmp/french_data.json for generate_french_pdf.py consumption.

IMPORTANT: Thematic tags are based on the OPENING PHASE (first 15 moves)
to avoid false positives from random middlegame/endgame moves.
"""

import re
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_pgn import load_games

PGN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'games.pgn')
MOVE_CUTOFF = 15


def get_raw_text(pgn_path, chapter_url):
    """Get full raw text for a game by chapter URL."""
    with open(pgn_path) as f:
        content = f.read()
    games = re.split(r'\n\n(?=\[Event)', content)
    for g in games:
        if chapter_url and chapter_url in g:
            return g
    return ''


def get_annotations(raw_text):
    """Extract all annotation comments from raw game text."""
    return ' '.join(re.findall(r'\{([^}]*)\}', raw_text))


def has_move_early(moves, pattern, max_move=MOVE_CUTOFF):
    """Check if a move pattern appears in the first N moves."""
    for num, move in moves:
        if num > max_move:
            break
        if re.match(pattern, move):
            return True
    return False


def has_move_any(moves, pattern):
    """Check if a move appears anywhere in the game."""
    for num, move in moves:
        if re.match(pattern, move):
            return True
    return False


def move_number_of(moves, pattern, max_move=999):
    """Return the move number of first occurrence of pattern, or 0."""
    for num, move in moves:
        if num > max_move:
            break
        if re.match(pattern, move):
            return num
    return 0


def first_n_moves_set(moves, n=10):
    """Return set of move strings from the first N moves."""
    return set(m for num, m in moves if num <= n)


def classify_variation(game, raw_text):
    """Classify the French variation from chapter name and moves."""
    ch = game['chapter'].lower()
    wm = game['wm']  # white = opponent
    bm = game['bm']  # black = us (sterkurstrakur)

    # Check first moves
    first_white = wm[0][1] if wm else ''
    second_white = wm[1][1] if len(wm) > 1 else ''

    # Winawer: we play ...Bb4
    has_bb4 = has_move_early(bm, r'Bb4\+?', 10)

    if 'winawer advanced' in ch or ('winawer' in ch and 'advanced' in ch):
        return 'winawer_advanced'
    elif 'winawer exchange' in ch:
        return 'winawer_exchange'
    elif 'winawer' in ch and 'ne2' in ch:
        return 'winawer_ne2_gambit'
    elif 'winawer' in ch and ('transpos' in ch):
        return 'winawer_transposition'
    elif has_bb4 and 'winawer' in ch:
        return 'winawer_other'
    elif 'advanced' in ch:
        return 'advanced'
    elif 'exchange' in ch:
        return 'exchange'
    elif 'tarrasch' in ch:
        return 'tarrasch'
    elif 'kia' in ch or 'king' in ch:
        return 'kia'
    else:
        return 'other'


def tag_french_game(game, raw_text):
    """Tag a French Defense game (sterkurstrakur as Black)."""
    tags = set()
    ann = get_annotations(raw_text)
    ann_lower = ann.lower()
    wm = game['wm']  # white = opponent
    bm = game['bm']  # black = us
    chapter = game['chapter'].lower()

    # === VARIATION CLASSIFICATION ===
    variation = classify_variation(game, raw_text)
    tags.add(f'var_{variation}')

    # Broader categories
    if variation.startswith('winawer'):
        tags.add('winawer')
    if variation in ('advanced', 'winawer_advanced'):
        tags.add('advanced_family')
    if variation in ('exchange', 'winawer_exchange'):
        tags.add('exchange_family')

    # === THE BAD LSB PROBLEM ===

    # b6 + Ba6 (trade bad LSB — Winawer plan)
    has_b6 = has_move_early(bm, r'b6', MOVE_CUTOFF)
    has_ba6 = has_move_early(bm, r'Ba6', 20)
    has_nxa6 = has_move_early(bm, r'Nxa6', 25)
    if has_b6 and has_ba6:
        tags.add('lsb_ba6_trade')
    if has_nxa6:
        tags.add('nxa6_reroute')

    # LSB to diagonal (Bg4, Bf5, Be6) — exchange/aggressive plans
    has_bg4 = has_move_early(bm, r'Bg4', MOVE_CUTOFF)
    has_bf5 = has_move_early(bm, r'Bf5', MOVE_CUTOFF)
    has_be6 = has_move_early(bm, r'Be6', MOVE_CUTOFF)
    if has_bg4:
        tags.add('lsb_bg4')
    if has_bf5:
        tags.add('lsb_bf5')
    if has_be6:
        tags.add('lsb_be6')
    if has_bg4 or has_bf5 or has_be6:
        tags.add('lsb_developed')

    # LSB traded on h7-b1 diagonal (exchange variation)
    # Check for Bxd3, Bxf1, or similar trades
    if has_move_any(bm, r'Bxd3') or has_move_any(bm, r'Bxf1'):
        tags.add('lsb_traded_diagonal')

    # Bd7-Bb5 trade attempt (mentioned in annotations)
    has_bd7 = has_move_early(bm, r'Bd7', MOVE_CUTOFF)
    has_bb5 = has_move_early(bm, r'Bb5', 20)
    if has_bd7 and has_bb5:
        tags.add('lsb_bd7_bb5')
    if has_bd7:
        tags.add('lsb_bd7')

    # === ADVANCED VARIATION PLANS ===

    # Qb6 pressure on d4/b2
    has_qb6 = has_move_early(bm, r'Qb6', MOVE_CUTOFF)
    if has_qb6:
        tags.add('qb6_pressure')

    # Nc6 pressure on d4
    has_nc6 = has_move_early(bm, r'Nc6', MOVE_CUTOFF)
    if has_nc6:
        tags.add('nc6_develop')

    # c5 pawn break (key in advanced/Tarrasch)
    has_c5 = has_move_early(bm, r'c5', MOVE_CUTOFF)
    if has_c5:
        tags.add('c5_break')

    # cxd4 exchange
    has_cxd4 = has_move_early(bm, r'cxd4', MOVE_CUTOFF)
    if has_cxd4:
        tags.add('cxd4_exchange')

    # Ne7 development (common in both Winawer and exchange)
    has_ne7 = has_move_early(bm, r'Ne7', MOVE_CUTOFF)
    if has_ne7:
        tags.add('ne7_develop')

    # f5 break (attacking the chain)
    has_f5 = has_move_early(bm, r'f5', 20)
    if has_f5:
        tags.add('f5_break')

    # f6 (controls e5/g5, prepares pawn storm)
    has_f6 = has_move_early(bm, r'f6', MOVE_CUTOFF)
    if has_f6:
        tags.add('f6_control')

    # Qb6 + Nc6 combined pressure on d4 (advanced plan)
    if has_qb6 and has_nc6:
        tags.add('d4_pressure')

    # b2 pawn grab (opponent blunders)
    has_qxb2 = has_move_any(bm, r'Qxb2')
    has_qxc3 = has_move_any(bm, r'Qxc3')
    if has_qxb2:
        tags.add('b2_grab')
    if has_qxb2 or has_qxc3:
        tags.add('pawn_grab')

    # === EXCHANGE VARIATION SUB-PLANS ===

    # Stonewall attempt in exchange
    has_f5_sw = has_move_early(bm, r'f5', 15)
    sw_ref = 'sw' in chapter or 'stonewall' in chapter
    if has_f5_sw and 'exchange_family' in tags:
        tags.add('exchange_sw_attempt')
    if sw_ref:
        tags.add('sw_reference')

    # Aggressive exchange: Bd6 + (Bg4/Bf5/Be6) + Qd7 + O-O-O
    has_bd6 = has_move_early(bm, r'Bd6', 10)
    has_qd7 = has_move_early(bm, r'Qd7', MOVE_CUTOFF)
    has_ooo = has_move_any(bm, r'O-O-O')
    has_oo = has_move_any(bm, r'O-O')

    if has_bd6 and has_ooo:
        tags.add('exchange_aggressive')
    if has_bd6 and has_ooo and has_qd7:
        tags.add('exchange_aggressive_full')

    # Conservative exchange: Bd6 + c6 + Nf6 + O-O
    has_nf6 = has_move_early(bm, r'Nf6', 10)
    has_c6 = has_move_early(bm, r'c6', 10)
    if has_bd6 and has_oo and has_c6 and has_nf6 and not has_ooo:
        tags.add('exchange_conservative')

    # Conservative sub-patterns
    if 'exchange_conservative' in tags or ('exchange_family' in tags and has_oo and not has_ooo):
        # Re8 open file pressure
        has_re8 = has_move_early(bm, r'Re8', 20)
        if has_re8:
            tags.add('cons_re8_file')

        # Qc7 battery (queen behind bishop on c7-h2 diagonal)
        has_qc7 = has_move_early(bm, r'Qc7', 20)
        if has_qc7:
            tags.add('cons_qc7_battery')

        # Nbd7 flexible knight (supports Ne5/Nc5, prepares Qc7)
        has_nbd7 = has_move_early(bm, r'Nbd7', 20) or has_move_early(bm, r'Nd7', 20)
        if has_nbd7:
            tags.add('cons_nbd7')

        # Queenside pawn expansion (b5/a5 push)
        has_b5 = has_move_any(bm, r'b5')
        has_a5 = has_move_any(bm, r'a5')
        if has_b5 or has_a5:
            tags.add('cons_qs_expansion')

    # General O-O vs O-O-O
    if has_ooo:
        tags.add('castle_queenside')
    elif has_oo:
        tags.add('castle_kingside')

    # h6 luft / "snork"
    has_h6 = has_move_early(bm, r'h6', 20)
    if has_h6:
        tags.add('h6_snork')

    # === OPPONENT DISRUPTIONS IN EXCHANGE ===

    # Qe2+ / Qh5+ early check
    opp_qe2 = has_move_early(wm, r'Qe2\+?', 10)
    opp_qh5 = has_move_early(wm, r'Qh5\+?', 10)
    if opp_qe2:
        tags.add('opp_qe2_check')
    if opp_qh5:
        tags.add('opp_qh5_check')
    if opp_qe2 or opp_qh5:
        tags.add('opp_queen_check')

    # Nc3 (attacks d5, common disruption)
    opp_nc3 = has_move_early(wm, r'Nc3', 10)
    if opp_nc3:
        tags.add('opp_nc3')

    # c4 (attacks d5, strong disruption)
    opp_c4 = has_move_early(wm, r'c4', 10)
    if opp_c4:
        tags.add('opp_c4')

    # Bc4/Bb3 (pressure on d5)
    opp_bc4 = has_move_early(wm, r'Bc4', 10)
    opp_bb3 = has_move_early(wm, r'Bb3', 15)
    if opp_bc4 or opp_bb3:
        tags.add('opp_bc4_bb3')

    # Re1+ (rook check on open e-file)
    opp_re1 = has_move_early(wm, r'Re1\+?', MOVE_CUTOFF)
    if opp_re1:
        tags.add('opp_re1_check')

    # Bg5 (pins knight)
    opp_bg5 = has_move_early(wm, r'Bg5', MOVE_CUTOFF)
    if opp_bg5:
        tags.add('opp_bg5_pin')

    # h3 waste of time
    opp_h3 = has_move_early(wm, r'h3', 10)
    if opp_h3:
        tags.add('opp_h3_tempo')

    # Nf3 (blocks Qh5, may enable SW)
    opp_nf3 = has_move_early(wm, r'N[gbd]?f3', 10)
    if opp_nf3:
        tags.add('opp_nf3')

    # === WINAWER SPECIFIC ===

    has_bb4 = has_move_early(bm, r'Bb4\+?', 10)
    if has_bb4:
        tags.add('bb4_pin')

    # Winawer Ne2: Ba5 retreat (don't take on c3 — knight recaptures cleanly)
    has_ba5 = has_move_early(bm, r'Ba5', 15)
    if has_ba5 and variation == 'winawer_ne2_gambit':
        tags.add('winawer_ne2_ba5')

    # Nxa6 → Nb8 → Nc6 knight reroute
    has_nb8 = has_move_early(bm, r'Nb8', 25)
    if has_nxa6 and has_nb8:
        tags.add('na6_nb8_nc6_reroute')

    # === TARRASCH PATTERNS ===

    # Early kingside castling in Tarrasch (main c5 plan)
    if variation == 'tarrasch':
        oo_move = move_number_of(bm, r'O-O$', 15)
        if oo_move and oo_move <= 12:
            tags.add('tarrasch_early_castle')

    # === SIDELINE CLASSICAL SETUP ===

    # Classical setup in sidelines: c5 + Nc6 (stick to what we know)
    if variation in ('other', 'kia'):
        if has_c5 and has_nc6:
            tags.add('sideline_classical')

    # === PAWN STORM (aggressive exchange) ===

    # g5 push
    has_g5 = has_move_early(bm, r'g5', 25)
    if has_g5:
        tags.add('g5_push')

    # h5 push
    has_h5 = has_move_early(bm, r'h5', 25)
    if has_h5:
        tags.add('h5_push')

    if (has_g5 or has_h5) and has_ooo:
        tags.add('pawn_storm')

    # === KNIGHT VS BAD BISHOP ENDGAME ===
    # Check if game went into an endgame with our knight vs opponent's bishop
    if re.search(r'knight.*vs.*bishop|N.*vs.*B.*end|bad.*bishop.*end|good.*knight.*bad.*bishop|N.*v.*B.*end', ann_lower):
        tags.add('knight_vs_bishop_endgame')

    # === BISHOP PAIR ===
    if re.search(r'bishop pair', ann_lower):
        tags.add('bishop_pair_advantage')

    # === STRUCTURAL ===

    # Quick win
    if game['total'] <= 20:
        tags.add('quick_win')

    # Long game (endgame likely)
    if game['total'] >= 40:
        tags.add('long_game')

    # Result
    result = game['result']
    if result == '0-1':
        tags.add('win')
    elif result == '1-0':
        tags.add('loss')
    else:
        tags.add('draw')

    return list(tags)


def main():
    _, french_games = load_games(PGN, 'sterkurstrakur')

    # Tag all games
    for g in french_games:
        raw = get_raw_text(PGN, g['url'])
        g['tags'] = tag_french_game(g, raw)
        g['variation'] = classify_variation(g, raw)

    # Output stats
    print(f"Tagged {len(french_games)} French games")

    tags = {}
    for g in french_games:
        for t in g['tags']:
            tags[t] = tags.get(t, 0) + 1
    print("\nAll tags:")
    for t, c in sorted(tags.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    # Variation breakdown
    from collections import Counter
    vars_count = Counter(g['variation'] for g in french_games)
    print("\nVariations:")
    for v, c in vars_count.most_common():
        print(f"  {v}: {c}")

    # Write JSON
    data = {'games': french_games}
    with open('/tmp/french_data.json', 'w') as f:
        json.dump(data, f, default=str)
    print(f"\nWrote /tmp/french_data.json")


if __name__ == '__main__':
    main()
