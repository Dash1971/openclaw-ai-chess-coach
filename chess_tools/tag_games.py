#!/usr/bin/env python3
"""
Tag wonestall Stonewall games with thematic categories.
Outputs /tmp/sw_data.json for generate_pdf.py consumption.

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
MOVE_CUTOFF = 15  # Only consider first 15 moves for thematic tagging


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


def moves_in_range(moves, max_move=MOVE_CUTOFF):
    """Filter moves to only those within the cutoff."""
    return [(n, m) for n, m in moves if n <= max_move]


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
    """Return the move number of first occurrence of pattern (within cutoff), or 0."""
    for num, move in moves:
        if num > max_move:
            break
        if re.match(pattern, move):
            return num
    return 0


def first_n_moves_set(moves, n=10):
    """Return set of move strings from the first N moves."""
    return set(m for num, m in moves if num <= n)


def tag_white_game(game, raw_text):
    """Tag a white stonewall game with thematic categories."""
    tags = set()
    ann = get_annotations(raw_text)
    ann_lower = ann.lower()
    wm = game['wm']  # white moves (all)
    bm = game['bm']  # black (opponent) moves (all)
    chapter = game['chapter'].lower()

    # Early moves for structure detection
    opp_first10 = first_n_moves_set(bm, 10)
    our_first10 = first_n_moves_set(wm, 10)

    # === OPPONENT STRUCTURE DETECTION (first 10 moves) ===

    # Opponent played ...d5 in first 10? (NOT KID-like)
    opp_d5_early = 'd5' in opp_first10
    # Opponent played ...d6 in first 10? (passive/KID-like)
    opp_d6_early = has_move_early(bm, r'd6', 10)
    # Opponent played ...g6 or ...Bg7 in first 10? (fianchetto)
    opp_fianchetto = has_move_early(bm, r'(g6|Bg7)', 10)
    # Opponent played ...f5 in first 10? (Dutch/symmetrical)
    opp_f5_early = has_move_early(bm, r'f5', 10)
    # Opponent played ...e6 in first 10?
    opp_e6_early = has_move_early(bm, r'e6', 10)

    # KID-like: fianchetto + NOT ...d5 (passive center)
    opp_kid_like = opp_fianchetto and not opp_d5_early

    # === ATTACK PATTERNS (first 15 moves for setup, any for execution) ===

    # Ne5 outpost
    if has_move_early(wm, r'Ne5'):
        tags.add('ne5')

    # g4 kingside storm (in first 20 moves — this is a middlegame plan)
    if has_move_early(wm, r'g4', 20):
        tags.add('g4_storm')

    # e4 central break (expanded tagging for dedicated section)
    e4_move_num = move_number_of(wm, r'e4', 999)  # any move
    if e4_move_num > 0 and e4_move_num <= 20:
        tags.add('e4_break')

        # --- Trigger sub-tags ---

        # Opponent played ...c4 before e4 (locks QS, frees our e-pawn)
        opp_c4_move = move_number_of(bm, r'c4', e4_move_num)
        if opp_c4_move > 0 and opp_c4_move < e4_move_num:
            tags.add('e4_after_c4')

        # Ne5 still on the board when e4 is played (not captured)
        ne5_move = move_number_of(wm, r'Ne5', e4_move_num)
        opp_nxe5 = has_move_any([(n,m) for n,m in bm if n <= e4_move_num], r'(Nxe5|Bxe5|fxe5|dxe5)')
        if ne5_move > 0 and not opp_nxe5:
            tags.add('e4_ne5_on_board')

        # Opponent not castled when e4 is played
        opp_castled_move = move_number_of(bm, r'O-O(-O)?', e4_move_num)
        if opp_castled_move == 0:
            tags.add('e4_opp_not_castled')

        # Passive/KID opponent setup
        if opp_kid_like:
            tags.add('e4_vs_kid')

        # LSB traded before e4
        opp_bxd3 = has_move_any([(n,m) for n,m in bm if n < e4_move_num], r'Bxd3')
        opp_bxc2 = has_move_any([(n,m) for n,m in bm if n < e4_move_num], r'Bxc2')
        if opp_bxd3 or opp_bxc2:
            tags.add('e4_lsb_traded')

        # --- Plan sub-tags (from annotations) ---

        # Blast open center
        if re.search(r'blast.*open|open.*position|open.*center|superior.*coordination', ann_lower):
            tags.add('e4_blast_center')

        # Free LSB diagonal
        if re.search(r'free.*bishop|free.*dsb|free.*lsb|open.*diagonal|unleash.*dsb|unleash.*bishop', ann_lower):
            tags.add('e4_free_bishop')

        # Plan B when Ne5 not taken
        if re.search(r'plan b|doesn.t capture|doesn.t take.*knight|if our opponent doesn.t', ann_lower):
            tags.add('e4_plan_b')

        # Eliminate weakness (e3 pawn)
        if re.search(r'getting rid.*weakness|rid.*our weakness|eliminate.*weakness', ann_lower):
            tags.add('e4_eliminate_weakness')

        # Take space / push opponent back
        if re.search(r'take space|gain space|push.*back|aggressive|passively.*elect', ann_lower):
            tags.add('e4_take_space')

        # Discovered attack
        if re.search(r'discover.*attack|discovering.*attack|discover.*queen', ann_lower):
            tags.add('e4_discovered_attack')

        # Threaten pawn fork
        if re.search(r'threaten.*fork|pawn fork|threatening.*Nxc6.*e5|fork', ann_lower):
            tags.add('e4_pawn_fork')

    # Qf3 setup
    if has_move_early(wm, r'Qf3', 20):
        tags.add('qf3')

    # Qh5
    if has_move_early(wm, r'Qh5', 20):
        tags.add('qh5')

    # Bc2 battery
    if has_move_early(wm, r'Bc2', 20):
        tags.add('bc2_battery')

    # Early f4 as prophylaxis vs ...Bg4 (keeping Nf3 available)
    f4_move = move_number_of(wm, r'f4', 8)
    if f4_move > 0 and re.search(r'bg4.*nf3|meet.*bg4.*nf3|able to play nf3|threatening bg4', ann_lower):
        tags.add('early_f4_bg4')

    # Queen support moves guarding the LSB / e4 square before committing
    qe1_move = move_number_of(wm, r'Qe1', 20)
    qe2_move = move_number_of(wm, r'Qe2', 20)
    qc2_move = move_number_of(wm, r'Qc2', 20)
    if (qe1_move > 0 or qe2_move > 0 or qc2_move > 0) and re.search(
        r'watch over.*lsb|guard.*lsb|light.?square.*bishop|defend.*e.?file|defend.*e4|guard.*e4|prevent ne4|queen is needed.*lsb|queen is needed.*e4|keep watch over the lsb',
        ann_lower,
    ):
        tags.add('queen_guard_e4')

    # Quick win
    if game['total'] <= 20:
        tags.add('quick_win')

    # Nd2 before Nf3
    nd2_move = move_number_of(wm, r'Nd2', MOVE_CUTOFF)
    nf3_move = move_number_of(wm, r'N[gbd]?f3', MOVE_CUTOFF)
    if nd2_move > 0 and (nf3_move == 0 or nd2_move < nf3_move):
        tags.add('nd2_first')
    if nd2_move > 0 and opp_f5_early and re.search(r"can.?t keep.*e4|can.?t prevent ne4|prevent ne4 anyway|didn.?t prioritize nd2|nd2 is futile", ann_lower):
        tags.add('nd2_futile_symmetrical')

    # === Bxh7+ — distinguish true sacrifice from supported attack ===
    bxh7_move = move_number_of(wm, r'Bxh7\+?', 999)
    if bxh7_move > 0:
        tags.add('bxh7_attack')
        # Check if a rook reached the h-file BEFORE Bxh7 (making it supported)
        rook_on_h = False
        for n, m in wm:
            if n < bxh7_move and re.match(r'R[a-h]?h\d', m):
                rook_on_h = True
                break
        # Also check if queen was on h-file before
        queen_on_h = False
        for n, m in wm:
            if n < bxh7_move and re.match(r'Qh\d', m):
                queen_on_h = True
                break
        if not rook_on_h and not queen_on_h:
            tags.add('bxh7_sac')
        else:
            tags.add('bxh7_supported')

    # === Bxh6 DSB ATTACK ===
    # DSB takes h6 pawn — rips open kingside (not always a true sac)
    if has_move_any(wm, r'Bxh6'):
        tags.add('bxh6_attack')

    # Exchange sac on f3 / rook sac motifs once the h-file and bishops are live
    if has_move_any(wm, r'Rxf3[+#]?') or re.search(r'rxf3|rook sac|exchange sac', ann_lower):
        tags.add('rxf3_sac')

    # === DSB MANEUVER ===
    bd2_move = move_number_of(wm, r'Bd2', MOVE_CUTOFF)
    be1_move = move_number_of(wm, r'Be1', 20)
    bh4_move = move_number_of(wm, r'Bh4', 25)

    if bd2_move > 0 and be1_move > 0:
        tags.add('dsb_maneuver')
        if bh4_move > 0:
            tags.add('dsb_maneuver_full')

    # Also tag from chapter name/annotations
    if re.search(r'DSB maneuver|dark.?square.?bishop.?maneuver', ann, re.I) or 'dsb maneuver' in chapter:
        tags.add('dsb_maneuver')

    # === g4 SUB-THEMES (must have g4 in first 20 moves) ===

    has_g4 = has_move_early(wm, r'g4', 20)

    # g4 vs e6 (opponent locked LSB with e6 in first 10)
    if has_g4 and opp_e6_early:
        tags.add('g4_vs_e6')
    if 'vs e6' in chapter and 'g4' in chapter:
        tags.add('g4_vs_e6')

    # g4 vs symmetrical SW (opponent played ...f5 in first 10)
    if has_g4 and opp_f5_early:
        tags.add('g4_vs_symmetrical')
    if ('symmetrical' in chapter or 'vs sw' in chapter or 'dutch' in chapter) and 'g4' in chapter:
        tags.add('g4_vs_symmetrical')

    # g4 after Bxf3 knight trade — BOTH moves must actually occur
    opp_bxf3_early = has_move_early(bm, r'Bxf3', 12)
    if has_g4 and opp_bxf3_early:
        tags.add('g4_after_bxf3')
    # Also tag from chapter name BUT only if g4 actually played
    if 'bxf3' in chapter and has_g4:
        tags.add('g4_after_bxf3')

    # g4 with Kh1/Rg1 preparation (both within first 20)
    if has_g4 and (has_move_early(wm, r'Kh1', 20) or has_move_early(wm, r'Rg1', 20)):
        tags.add('g4_kh1_rg1')

    # === DSB MANEUVER SUB-THEMES ===

    # DSB maneuver vs symmetrical SW (opponent played ...f5 early)
    if 'dsb_maneuver' in tags and opp_f5_early:
        tags.add('dsb_vs_symmetrical')
    if 'dsb_maneuver' in tags and ('symmetrical' in chapter or 'dutch' in chapter or 'vs sw' in chapter):
        tags.add('dsb_vs_symmetrical')

    # DSB maneuver vs KID-like (passive center: fianchetto WITHOUT ...d5)
    if 'dsb_maneuver' in tags and opp_kid_like:
        tags.add('dsb_vs_kid')
    if (re.search(r'KID|King.?Indian', chapter) or re.search(r'KID|King.?Indian', ann, re.I)):
        if 'dsb_maneuver' in tags or re.search(r'DSB|maneuver|manoeuv', ann, re.I):
            tags.add('dsb_vs_kid')

    # === OPPONENT THREATS (first 12 moves — opening phase) ===

    # Bb7 in first 12 (fianchetto threat, not random middlegame bishop move)
    if has_move_early(bm, r'Bb7', 12):
        tags.add('opp_bb7')

    # b6 in first 12
    if has_move_early(bm, r'b6', 12):
        tags.add('opp_b6')

    # Nc6 in first 10
    if has_move_early(bm, r'Nc6', 10):
        tags.add('opp_nc6')

    # Qb6 in first 15
    if has_move_early(bm, r'Qb6', MOVE_CUTOFF):
        tags.add('opp_qb6')
    if 'qb6' in chapter:
        tags.add('opp_qb6')

    # Bd6 + c5 in first 12
    opp_c5_early = has_move_early(bm, r'c5', 12)
    opp_bd6_early = has_move_early(bm, r'Bd6', 12)
    if opp_c5_early and opp_bd6_early:
        tags.add('opp_bd6_c5')

    # Ba6 forced trade (in first 20 — this can develop a bit later)
    if has_move_early(bm, r'Ba6', 20):
        tags.add('opp_ba6_trade')
    # Also from annotations about the threat
    if re.search(r'Ba6.*forc|forc.*Ba6|avoid.*Ba6|threatening Ba6', ann, re.I):
        tags.add('opp_ba6_trade')

    # a5/b5 pawn pushes threatening Ba6 (in first 15)
    if (has_move_early(bm, r'a5', MOVE_CUTOFF) or has_move_early(bm, r'b5', MOVE_CUTOFF)):
        if re.search(r'Ba6|bishop.*trade|trade.*bishop', ann_lower):
            tags.add('opp_ba6_trade')

    # === Ne5 BEFORE CASTLING ===
    ne5_move = move_number_of(wm, r'N[a-h]?e5', MOVE_CUTOFF)
    castle_move = move_number_of(wm, r'O-O(-O)?', 999)
    if ne5_move > 0 and (castle_move == 0 or ne5_move < castle_move):
        tags.add('ne5_before_castle')
        # Sub-classify the reason
        # 1. Opponent wasted time with queenside pawn pushes (a/b pawns in first 8 moves)
        opp_qs_pushes = sum(1 for n, m in bm if n <= 8 and re.match(r'[ab]\d', m))
        if opp_qs_pushes >= 2:
            tags.add('ne5_bc_punish_tempo')
        # 2. Blocking bishop attacking f4 (opponent has bishop on d6 or threatening cxd4/Bxf4)
        opp_bd6 = has_move_early(bm, r'Bd6', 10)
        opp_c5 = has_move_early(bm, r'c5', 10)
        if opp_bd6 or opp_c5:
            tags.add('ne5_bc_block_bishop')
        # 3. Targeting opponent's bishop on g6 (opponent played ...Bg6 or ...g6+Bg4-g6 pattern)
        opp_bg6 = has_move_early(bm, r'Bg6', 12)
        if opp_bg6:
            tags.add('ne5_bc_target_bg6')
        # 4. Opponent threatening f5
        if re.search(r'f5|planning.*f5|push.*f5', ann_lower):
            tags.add('ne5_bc_prevent_f5')
        # 5. Disrupted castling (Qb6 pin or other disruption)
        if has_move_early(bm, r'Qb6', 10):
            tags.add('ne5_bc_disrupted')
        # Also check annotations for reasons
        if re.search(r'punish|time.?wast|slow|queenside pawn push', ann_lower):
            tags.add('ne5_bc_punish_tempo')
        if re.search(r'block.*bishop.*f.?pawn|block.*attack.*f|cxd4.*exd4', ann_lower):
            tags.add('ne5_bc_block_bishop')
        if re.search(r'target.*bishop.*g6|take the bishop|hit.*bishop', ann_lower):
            tags.add('ne5_bc_target_bg6')
        if re.search(r'can.?t.*castle|disrupt.*castle|pin.*castle', ann_lower):
            tags.add('ne5_bc_disrupted')

    # === STRUCTURAL ===

    # vs fianchetto (first 10)
    if opp_fianchetto:
        tags.add('vs_fianchetto')

    # vs e5 break (first 15)
    if has_move_early(bm, r'e5', MOVE_CUTOFF):
        tags.add('vs_e5')

    # vs symmetrical/Dutch (opponent f5 in first 10)
    if opp_f5_early:
        tags.add('vs_symmetrical')

    return list(tags)


def tag_black_game(game, raw_text):
    """Tag a black stonewall game with thematic categories."""
    tags = set()
    ann = get_annotations(raw_text)
    ann_lower = ann.lower()
    wm = game['wm']  # white (opponent) moves
    bm = game['bm']  # black (our) moves
    chapter = game['chapter'].lower()

    opp_first10 = first_n_moves_set(wm, 10)

    # === OPPONENT OPENING TYPE ===
    first_white = wm[0][1] if wm else ''
    if first_white == 'e4':
        tags.add('vs_e4')
    elif first_white == 'd4':
        if has_move_early(wm, r'Bf4', 10):
            tags.add('vs_london')
        elif has_move_early(wm, r'c4', 10):
            tags.add('vs_d4_c4')
        else:
            tags.add('vs_d4_other')
    else:
        tags.add('vs_other')

    # === OPPONENT STRUCTURE DETECTION ===
    # Opponent committed center pawns (d4+e4 or at least e4)?
    opp_e4_early = 'e4' in opp_first10
    opp_d4_early = 'd4' in opp_first10
    # Opponent played g3 (KIA-like)?
    opp_g3_early = has_move_early(wm, r'g3', 10)
    # Opponent played f4 (symmetrical)?
    opp_f4_early = has_move_early(wm, r'f4', 10)

    # KIA-like: g3 WITHOUT fully committed center (no d4+e4 together)
    # Or: passive center where opponent controls e4 from behind without pushing
    opp_kia_like = opp_g3_early and not (opp_e4_early and opp_d4_early)
    # Also Indian-style: opponent doesn't push central pawns to 4th rank
    opp_indian_like = not opp_e4_early and not opp_d4_early

    # === PAWN WALL ===
    has_d5 = has_move_early(bm, r'd5', 10)
    has_e6 = has_move_early(bm, r'e6', 10)
    has_f5 = has_move_early(bm, r'f5', MOVE_CUTOFF)
    has_c6 = has_move_early(bm, r'c6', MOVE_CUTOFF)
    if has_d5 and has_e6 and has_f5 and has_c6:
        tags.add('full_wall')

    # === ATTACK PATTERNS ===

    # Ne4 outpost
    if has_move_early(bm, r'Ne4', 20):
        tags.add('ne4')

    # e5 central break
    if has_move_early(bm, r'e5', 20):
        tags.add('e5_break')

    # g5 push
    if has_move_early(bm, r'g5', 20):
        tags.add('g5_push')

    # Bxh2 attack — ONLY match actual moves, NOT annotation text
    if has_move_any(bm, r'Bxh2\+?'):
        tags.add('bxh2_attack')

    # Quick win
    if game['total'] <= 20:
        tags.add('quick_win')

    # Queen reroute (first 20)
    if has_move_early(bm, r'Qe8', 20) or has_move_early(bm, r'Qe7', 20):
        tags.add('queen_reroute')

    # Early Nd7 prophylaxis against Ne5 — useful in some structures, but not automatic
    nd7_move = move_number_of(bm, r'Nd7', 15)
    if nd7_move > 0 and (re.search(r'stop(ping)? ne5|prevent ne5|allowing ne5', ann_lower) or 'nd7 to prevent ne5' in chapter):
        tags.add('nd7_prophylaxis')
        if re.search(r'cxd5|recaptur.*cxd5|forced.*cxd5|take back cxd5', ann_lower):
            tags.add('nd7_cxd5_liability')

    # === LSB MANEUVER ===
    bd7 = move_number_of(bm, r'Bd7', 20)
    be8 = move_number_of(bm, r'Be8', 25)
    bh5 = move_number_of(bm, r'Bh5', 30)

    if bd7 > 0 and be8 > 0:
        tags.add('lsb_maneuver')
        if bh5 > 0:
            tags.add('lsb_maneuver_full')
    if re.search(r'LSB maneuver|light.?square.?bishop.?maneuver|bad.?bishop.*(maneuver|manoeuv)', ann, re.I):
        tags.add('lsb_maneuver')
    if 'lsb maneuver' in chapter:
        tags.add('lsb_maneuver')

    # LSB vs symmetrical (opponent played f4 early)
    if 'lsb_maneuver' in tags and opp_f4_early:
        tags.add('lsb_vs_symmetrical')
    if 'lsb_maneuver' in tags and ('stonewall' in chapter or 'vs sw' in chapter):
        tags.add('lsb_vs_symmetrical')

    # LSB vs KIA-like (opponent passive center, g3 setup, Ne4 denied)
    if 'lsb_maneuver' in tags and opp_kia_like:
        tags.add('lsb_vs_kia')
    if re.search(r'KIA|King.?Indian.?Attack', ann, re.I) or ('kia' in chapter and 'lsb' in chapter):
        tags.add('lsb_vs_kia')
    # Also: opponent plays Indian-style (uncommitted center) with LSB maneuver
    if 'lsb_maneuver' in tags and opp_indian_like and not opp_f4_early:
        tags.add('lsb_vs_passive')

    # Opponent plays Ne5
    if has_move_early(wm, r'Ne5', 20):
        tags.add('opp_ne5')

    # === Ne4 BEFORE CASTLING ===
    ne4_move = move_number_of(bm, r'N[a-h]?e4', 25)
    castle_move_b = move_number_of(bm, r'O-O(-O)?', 999)
    if ne4_move > 0 and (castle_move_b == 0 or ne4_move < castle_move_b):
        tags.add('ne4_before_castle')
        # Sub-classify
        # 1. Blocking rook check on e-file (French exchange — open e-file)
        if 'vs_e4' in tags:
            tags.add('ne4_bc_block_check')
        if re.search(r'block.*check|check.*e.?file|rook.*check|Ne4.*block', ann_lower):
            tags.add('ne4_bc_block_check')
        # 2. Forcing the issue / tempo urgency
        if re.search(r'force the issue|tempo down|more direct|aggress', ann_lower):
            tags.add('ne4_bc_force_issue')
        # 3. Exploiting weak e4 (opponent's structure allows it)
        if re.search(r'weak.*e4|dominating.*e4|avoid.*symmetrical', ann_lower):
            tags.add('ne4_bc_exploit_weak')

    # Early Bd6 vs London
    if 'vs_london' in tags:
        bd6_move = move_number_of(bm, r'Bd6', 10)
        f5_move = move_number_of(bm, r'f5', 10)
        if bd6_move > 0 and (f5_move == 0 or bd6_move < f5_move):
            tags.add('early_bd6_london')

    return list(tags)


def main():
    white_games, black_games = load_games(PGN, 'wonestall')

    # Read raw texts once
    with open(PGN) as f:
        content = f.read()

    # Tag white games
    for g in white_games:
        raw = get_raw_text(PGN, g['url'])
        g['tags'] = tag_white_game(g, raw)

    # Tag black games
    for g in black_games:
        raw = get_raw_text(PGN, g['url'])
        g['tags'] = tag_black_game(g, raw)

    # Output stats
    print(f"Tagged {len(white_games)} white + {len(black_games)} black games")
    print(f"(Opening cutoff: {MOVE_CUTOFF} moves)")

    w_tags = {}
    for g in white_games:
        for t in g['tags']:
            w_tags[t] = w_tags.get(t, 0) + 1
    print("\nWhite tags:")
    for t, c in sorted(w_tags.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    b_tags = {}
    for g in black_games:
        for t in g['tags']:
            b_tags[t] = b_tags.get(t, 0) + 1
    print("\nBlack tags:")
    for t, c in sorted(b_tags.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    # Write JSON
    data = {
        'white_games': white_games,
        'black_games': black_games,
    }
    with open('/tmp/sw_data.json', 'w') as f:
        json.dump(data, f, default=str)
    print(f"\nWrote /tmp/sw_data.json")


if __name__ == '__main__':
    main()
