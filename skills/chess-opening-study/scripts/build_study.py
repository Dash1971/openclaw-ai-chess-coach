#!/usr/bin/env python3
"""
Chess Opening Study Builder
Extract and annotate French Defense or Stonewall games from any chess.com player.
Outputs clean PGN for lichess study import.

Usage:
    python3 build_study.py <username> <opening> [--max N] [--min-moves M] [--pgn-path PATH]

Arguments:
    username    chess.com username
    opening     'french' or 'stonewall'
    --max N     max games to include (default: 64)
    --min-moves minimum game length in moves (default: 20)
    --pgn-path  path to PGN file (default: opponents/<username>/games.pgn or <username>/games.pgn)

Output: opponents/<username>/<username>-<opening>-study.pgn
"""

import re
import os
import sys
import json
import argparse
from collections import Counter

WORKSPACE = os.path.expanduser('<workspace>')


# ═══════════════════════════════════════════════════════════════════════════════
# PGN PARSING (chess.com format)
# ═══════════════════════════════════════════════════════════════════════════════

def parse_chessdotcom_moves(text):
    """Parse chess.com PGN format with clock annotations."""
    clean = re.sub(r'\{[^}]*\}', '', text)
    clean = re.sub(r'\$\d+', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    white_moves, black_moves = [], []

    for m in re.finditer(r'(\d+)\.\s+(?!\.\.)(\S+)', clean):
        num, move = int(m.group(1)), m.group(2)
        if move in ('1-0', '0-1', '1/2-1/2', '*'):
            continue
        white_moves.append((num, move))

    for m in re.finditer(r'(\d+)\.\.\.\s*(\S+)', clean):
        num, move = int(m.group(1)), m.group(2)
        if move in ('1-0', '0-1', '1/2-1/2', '*'):
            continue
        black_moves.append((num, move))

    return white_moves, black_moves


def has_move(move_list, pattern, max_move=999):
    """Return move number of first match, or 0."""
    for num, move in move_list:
        if num > max_move:
            break
        if re.match(pattern + r'[+#]?$', move):
            return num
    return 0


def has_any_of(move_list, patterns, max_move=999):
    """Check if any of the patterns match."""
    for p in patterns:
        n = has_move(move_list, p, max_move)
        if n:
            return n
    return 0


# ═══════════════════════════════════════════════════════════════════════════════
# OPENING DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def is_french(wm, bm, player_color):
    """Check if game is a French Defense. Returns True if 1.e4 e6 2.d4 d5 pattern."""
    wd = {n: m for n, m in wm}
    bd = {n: m for n, m in bm}
    return wd.get(1) == 'e4' and bd.get(1) == 'e6'


def classify_french(wm, bm):
    """Classify French variation from actual moves."""
    wd = {n: m for n, m in wm}
    bd = {n: m for n, m in bm}

    w2, w3 = wd.get(2, ''), wd.get(3, '')
    b3 = bd.get(3, '')

    if w2 != 'd4':
        if w2 in ('d3', 'Qe2'):
            return 'KIA/Sideline'
        if w2 == 'Nf3':
            for i in range(3, 6):
                if wd.get(i, '') == 'exd5':
                    return 'Exchange'
            return 'Other Sideline'
        return 'Other Sideline'

    if w3 == 'e5':
        return 'Advanced'
    if w3 == 'Nd2':
        for i in range(4, 7):
            if wd.get(i, '').startswith('exd'):
                return 'Tarrasch Open'
        return 'Tarrasch Closed'
    if w3 == 'Nc3':
        if b3 in ('Bb4', 'Bb4+'):
            return 'Winawer'
        if b3 == 'Nf6':
            return 'Classical'
        return 'Nc3 System'
    if w3 == 'exd5':
        return 'Exchange'

    # Nc3 on other moves
    for i in range(2, 6):
        if wd.get(i, '') == 'Nc3':
            for j in range(2, 8):
                if bd.get(j, '') in ('Bb4', 'Bb4+'):
                    return 'Winawer'
            return 'Classical'

    # Check for early exd5
    for i in range(2, 6):
        if wd.get(i, '') == 'exd5':
            return 'Exchange'

    return 'Other'


def is_stonewall(wm, bm, player_color):
    """Check if game has a Stonewall structure for the given color."""
    moves = wm if player_color == 'white' else bm

    if player_color == 'white':
        has_d4 = has_move(moves, r'd4', 10)
        has_e3 = has_move(moves, r'e3', 10)
        has_f4 = has_move(moves, r'f4', 15)
        return bool(has_d4 and has_e3 and has_f4)
    else:
        has_d5 = has_move(moves, r'd5', 10)
        has_e6 = has_move(moves, r'e6', 10)
        has_f5 = has_move(moves, r'f5', 15)
        return bool(has_d5 and has_e6 and has_f5)


def classify_stonewall(wm, bm, player_color):
    """Classify Stonewall sub-type."""
    opp_moves = bm if player_color == 'white' else wm

    if player_color == 'white':
        return 'White Stonewall'
    else:
        # Check if opponent played London (Bf4)
        if has_move(opp_moves, r'Bf4', 10):
            return 'Black SW (Anti-London)'
        return 'Black Stonewall'


# ═══════════════════════════════════════════════════════════════════════════════
# FRENCH ANNOTATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def annotate_french(variation, wm, bm, total_moves, player, opponent, elo, player_color):
    """Generate French annotations based on Aman's sterkurstrakur framework."""
    ann = {}
    is_black = player_color == 'black'
    pm = bm if is_black else wm  # player's moves
    om = wm if is_black else bm  # opponent's moves

    # Header
    color_str = "Black" if is_black else "White"
    header = f"French {variation} — {player} ({color_str}) vs {opponent} ({elo}). "

    frameworks = {
        'Exchange': "KEY FRAMEWORK: Aman's three-plan decision tree — (1) Stonewall attempt (rarely scales), (2) Aggressive O-O-O with pawn storm, (3) Conservative O-O.",
        'Advanced': "KEY FRAMEWORK: Attack the chain at its base. Qb6 + Nc6 + c5 = triple pressure on d4. Watch for b2 blunder and Ne7→f5 break.",
        'Winawer': "KEY FRAMEWORK: Bb4 100% after Nc3. Plans: Ba6 trade (solve bad LSB), Nxa6→Nb8→Nc6 reroute, h5 kingside counter.",
        'Tarrasch Open': "KEY FRAMEWORK: Nd2 avoids Winawer pin. Respond with c5. IQP gives active piece play.",
        'Tarrasch Closed': "KEY FRAMEWORK: Nd2 without early exchange. c5 challenge still key.",
        'Classical': "KEY FRAMEWORK: Bg5 creates tension. Watch for Burn variation (dxe4) and the eternal LSB problem.",
    }
    header += frameworks.get(variation, "Sideline — watch for natural development and center control.")
    ann['pre'] = header

    ann['1.b'] = "The French Defense."

    # Common annotations for Black French player
    if is_black:
        _french_black_annotations(ann, variation, wm, bm, total_moves)
    else:
        # Player is White against the French — annotate from defensive perspective
        ann['1.b'] = "The French — solid strategic choice by Black."

    return ann


def _french_black_annotations(ann, variation, wm, bm, total_moves):
    """Add French annotations when the study player is Black."""

    d5 = has_move(bm, r'd5', 5)
    if d5:
        ann[f'{d5}.b'] = "Claiming the center. The French pawn structure (e6+d5) is established."

    if variation == 'Exchange':
        _ann_exchange(ann, wm, bm, total_moves)
    elif variation == 'Advanced':
        _ann_advanced(ann, wm, bm, total_moves)
    elif variation == 'Winawer':
        _ann_winawer(ann, wm, bm, total_moves)
    elif 'Tarrasch' in variation:
        _ann_tarrasch(ann, wm, bm, total_moves, variation)
    elif variation == 'Classical':
        _ann_classical(ann, wm, bm, total_moves)

    # Universal
    ooo = has_move(bm, r'O-O-O', 25)
    oo = has_move(bm, r'O-O', 25)
    if ooo and variation != 'Exchange':
        ann[f'{ooo}.b'] = ann.get(f'{ooo}.b', '') + " Queenside castling — 17% of Aman's French games castle QS, enabling kingside aggression."
    if not oo and not ooo and total_moves > 25:
        ann['post'] = ann.get('post', '') + " Never castled — 23% of Aman's French games also skip castling (closed center)."
    if total_moves >= 45:
        ann['post'] = ann.get('post', '') + " Long game — watch for knight vs bad bishop endgame themes."


def _ann_exchange(ann, wm, bm, total):
    bg4 = has_move(bm, r'Bg4', 15)
    bf5 = has_move(bm, r'Bf5', 15)
    be6 = has_move(bm, r'Be6', 15)
    if bg4:
        ann[f'{bg4}.b'] = "Bg4! Activating the bad LSB — THE key Exchange French concept. Aman does this in nearly every Exchange game."
    if bf5:
        ann[f'{bf5}.b'] = "Bf5 — active LSB development. Critical to get this piece out in the Exchange."
    if be6:
        ann[f'{be6}.b'] = "Be6 — solid LSB square, supports d5."

    obg5 = has_move(wm, r'Bg5', 15)
    if obg5:
        ann[f'{obg5}.w'] = "Bg5 — pinning the knight. Aman's response: f6! ('wanted anyway')."
    f6 = has_move(bm, r'f6', 15)
    if f6 and obg5:
        ann[f'{f6}.b'] = "f6! Aman's recommendation vs Bg5 — controls e5/g5, prepares kingside push."

    ooo = has_move(bm, r'O-O-O', 20)
    if ooo:
        ann[f'{ooo}.b'] = "O-O-O! Aggressive plan — QS castle enables kingside pawn storm. Plan B in Aman's decision tree."
    f5 = has_move(bm, r'f5', 15)
    if f5 and not ooo:
        ann[f'{f5}.b'] = "f5 — Stonewall structure in the Exchange. Aman's Plan A, but 'won't scale past opponents who know what they're doing.'"

    bd6 = has_move(bm, r'Bd6', 10)
    if bd6:
        ann[f'{bd6}.b'] = "Bd6 — Aman prioritizes this as the first developing move in the Exchange."
    ne7 = has_move(bm, r'Ne7', 15)
    if ne7:
        ann[f'{ne7}.b'] = "Ne7 — flexible knight, can reroute to g6, f5, or c6."

    oqe2 = has_move(wm, r'Qe2', 10)
    if oqe2:
        ann[f'{oqe2}.w'] = "Qe2(+) — common Exchange disruption."
    onc3 = has_move(wm, r'Nc3', 10)
    if onc3:
        ann[f'{onc3}.w'] = "Nc3 — attacking d5. Appeared in 33 of Aman's 60 French games."
    oc4 = has_move(wm, r'c4', 10)
    if oc4:
        ann[f'{oc4}.w'] = "c4 — aggressive center expansion, pressuring d5."


def _ann_advanced(ann, wm, bm, total):
    e5w = has_move(wm, r'e5', 5)
    if e5w:
        ann[f'{e5w}.w'] = "e5 — the Advance. White gains space but creates a chain to attack."
    c5 = has_move(bm, r'c5', 10)
    if c5:
        ann[f'{c5}.b'] = "c5! Attacking the chain at its base — fundamental Advanced French."
    nc6 = has_move(bm, r'Nc6', 10)
    if nc6:
        ann[f'{nc6}.b'] = "Nc6 — piece pressure on d4. Combined with Qb6+c5: triple attack."
    qb6 = has_move(bm, r'Qb6', 15)
    if qb6:
        ann[f'{qb6}.b'] = "Qb6! Pressure on d4 and b2. In 6 Aman games, opponents blundered b2."
    qxb2 = has_move(bm, r'Qxb2', 30)
    if qxb2:
        ann[f'{qxb2}.b'] = "Qxb2! Grabbing the pawn — recurring Aman pattern."
    ne7 = has_move(bm, r'Ne7', 15)
    if ne7:
        ann[f'{ne7}.b'] = "Ne7 — heading to f5 (attacks d4)."
    f5 = has_move(bm, r'f5', 25)
    f6 = has_move(bm, r'f6', 25)
    if f6:
        ann[f'{f6}.b'] = "f6! Breaking e5 — undermines White's space advantage."
    elif f5:
        ann[f'{f5}.b'] = "f5 — undermining e5 from the other side."
    bd7 = has_move(bm, r'Bd7', 15)
    bb5 = has_move(bm, r'Bb5', 25)
    if bd7 and bb5:
        ann[f'{bb5}.b'] = "Bb5! Bd7→Bb5 maneuver to activate/trade the bad LSB."
    cxd4 = has_move(bm, r'cxd4', 15)
    if cxd4:
        ann[f'{cxd4}.b'] = "cxd4 — timing this capture correctly is key."


def _ann_winawer(ann, wm, bm, total):
    bb4 = has_move(bm, r'Bb4', 10)
    if bb4:
        ann[f'{bb4}.b'] = "Bb4! The Winawer — Aman plays this 100% after Nc3."
    bxc3 = has_move(bm, r'Bxc3', 10)
    if bxc3:
        ann[f'{bxc3}.b'] = "Bxc3+ — bishop for knight, doubling c-pawns. Plan: exploit dark squares."

    b6 = has_move(bm, r'b6', 20)
    ba6 = has_move(bm, r'Ba6', 25)
    if b6 and ba6:
        ann[f'{ba6}.b'] = "Ba6! Trading the bad LSB — THE Winawer solution."
    elif ba6:
        ann[f'{ba6}.b'] = "Ba6 — seeking to trade the bad LSB."

    nxa6 = has_move(bm, r'Nxa6', 25)
    nb8 = has_move(bm, r'Nb8', 30)
    if nxa6:
        ann[f'{nxa6}.b'] = "Nxa6 — beginning the knight reroute: Na6→Nb8→Nc6."
    if nb8 and nxa6:
        ann[f'{nb8}.b'] = "Nb8! Heading to c6 — looks passive but it's theory."

    h5 = has_move(bm, r'h5', 20)
    if h5:
        ann[f'{h5}.b'] = "h5! Prevents g4, stakes kingside space."
    qg4 = has_move(wm, r'Qg4', 10)
    if qg4:
        ann[f'{qg4}.w'] = "Qg4 — White's main Winawer attack. Expected and manageable."
    qxg7 = has_move(wm, r'Qxg7', 15)
    if qxg7:
        ann[f'{qxg7}.w'] = "Qxg7 — theory. Black gets compensation through active pieces."
    ne7 = has_move(bm, r'Ne7', 10)
    if ne7:
        ann[f'{ne7}.b'] = "Ne7 — flexible: can go f5 or g6."
    c5 = has_move(bm, r'c5', 10)
    if c5:
        ann[f'{c5}.b'] = "c5 — striking at d4 even in the Winawer."


def _ann_tarrasch(ann, wm, bm, total, variation):
    nd2 = has_move(wm, r'Nd2', 5)
    if nd2:
        ann[f'{nd2}.w'] = "Nd2 — the Tarrasch. Avoids Winawer pin but more passive."
    c5 = has_move(bm, r'c5', 10)
    if c5:
        ann[f'{c5}.b'] = "c5! Standard anti-Tarrasch — challenge d4 immediately."
    nc6 = has_move(bm, r'Nc6', 10)
    if nc6:
        ann[f'{nc6}.b'] = "Nc6 — developing with d4 pressure."
    if 'Open' in variation:
        qxd5 = has_move(bm, r'Qxd5', 10)
        if qxd5:
            ann[f'{qxd5}.b'] = "Qxd5 — Tarrasch Open. IQP compensated by active pieces."
        cxd4 = has_move(bm, r'cxd4', 10)
        if cxd4:
            ann[f'{cxd4}.b'] = "cxd4 — opening the position for piece activity."
    bd6 = has_move(bm, r'Bd6', 10)
    if bd6:
        ann[f'{bd6}.b'] = "Bd6 — active dark-squared bishop."
    nf6 = has_move(bm, r'Nf6', 10)
    if nf6:
        ann[f'{nf6}.b'] = "Nf6 — natural development, controlling e4."
    qb6 = has_move(bm, r'Qb6', 15)
    if qb6:
        ann[f'{qb6}.b'] = "Qb6 — targeting b2/d4, universal French motif."


def _ann_classical(ann, wm, bm, total):
    bg5 = has_move(wm, r'Bg5', 10)
    if bg5:
        ann[f'{bg5}.w'] = "Bg5 — the Classical. Pins Nf6 and creates tension."
    nf6 = has_move(bm, r'Nf6', 5)
    if nf6:
        ann[f'{nf6}.b'] = "Nf6 — defending d5."
    dxe4 = has_move(bm, r'dxe4', 10)
    if dxe4:
        ann[f'{dxe4}.b'] = "dxe4 — Burn Variation. Sharp, double-edged."
    be7 = has_move(bm, r'Be7', 10)
    if be7:
        ann[f'{be7}.b'] = "Be7 — breaking the Bg5 pin."
    gxf6 = has_move(bm, r'gxf6', 10)
    if gxf6:
        ann[f'{gxf6}.b'] = "gxf6! Doubled f-pawns but half-open g-file and bishop pair."
    c5 = has_move(bm, r'c5', 15)
    if c5:
        ann[f'{c5}.b'] = "c5 — standard break challenging d4."
    e5w = has_move(wm, r'e5', 10)
    if e5w:
        ann[f'{e5w}.w'] = "e5 — Advanced-like. Black should attack the chain."
    qb6 = has_move(bm, r'Qb6', 15)
    if qb6:
        ann[f'{qb6}.b'] = "Qb6 — pressure on d4/b2."
    f5 = has_move(bm, r'f5', 15)
    if f5:
        ann[f'{f5}.b'] = "f5 — seizing space aggressively."


# ═══════════════════════════════════════════════════════════════════════════════
# STONEWALL ANNOTATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def annotate_stonewall(variation, wm, bm, total_moves, player, opponent, elo, player_color):
    """Generate Stonewall annotations based on Aman's wonestall framework."""
    ann = {}
    is_white = player_color == 'white'
    pm = wm if is_white else bm
    om = bm if is_white else wm

    header = f"Stonewall ({variation}) — {player} ({'White' if is_white else 'Black'}) vs {opponent} ({elo}). "

    if is_white:
        header += "KEY FRAMEWORK: d4→e3→Bd3→f4. Plans: Ne5 (76%), g4 storm (31%), e4 break (40%), Bxh7+ sacrifice (12%). Nd2 protects d4 (82%)."
        ann['pre'] = header
        _ann_sw_white(ann, wm, bm, total_moves)
    else:
        header += "KEY FRAMEWORK: Pawns before pieces (76% play 4+ first). Ne4 is THE plan (81%, avg move 11). LSB maneuver: Bd7→Be8→Bh5."
        ann['pre'] = header
        _ann_sw_black(ann, wm, bm, total_moves)

    return ann


def _ann_sw_white(ann, wm, bm, total):
    d4 = has_move(wm, r'd4', 5)
    e3 = has_move(wm, r'e3', 10)
    bd3 = has_move(wm, r'Bd3', 10)
    f4 = has_move(wm, r'f4', 15)

    if bd3:
        ann[f'{bd3}.w'] = f"Bd3 — Aman plays this on move 3 in 61% of games. Early Bd3 is a Stonewall signature."
    if f4:
        ann[f'{f4}.w'] = "f4 — completing the Stonewall pawn wall (d4+e3+f4). The structure is set."

    ne5 = has_move(wm, r'Ne5', 20)
    if ne5:
        ann[f'{ne5}.w'] = "Ne5! THE primary Stonewall plan (76% of Aman's games). The knight is a monster on e5."
    nd2 = has_move(wm, r'Nd2', 15)
    if nd2:
        ann[f'{nd2}.w'] = "Nd2 — protecting d4 (82% of Aman's games). Frees the queen and prepares Ne5 via f3."

    g4 = has_move(wm, r'g4', 25)
    if g4:
        ann[f'{g4}.w'] = "g4! Kingside pawn storm — 31% of Aman's White SW games. Aggressive but requires preparation."
    e4 = has_move(wm, r'e4', 25)
    if e4:
        ann[f'{e4}.w'] = "e4! The central break — 40% of games. Opens the position when White has a space advantage."

    bxh7 = has_move(wm, r'Bxh7', 30)
    if bxh7:
        ann[f'{bxh7}.w'] = "Bxh7+! The Greek Gift sacrifice — appears in 12% of Aman's White SW games."

    qf3 = has_move(wm, r'Qf3', 20)
    qh5 = has_move(wm, r'Qh5', 20)
    if qf3:
        ann[f'{qf3}.w'] = "Qf3 — queen joins the kingside attack."
    if qh5:
        ann[f'{qh5}.w'] = "Qh5 — aggressive queen deployment targeting h7."

    # DSB never moves check
    dsb_moves = has_any_of(wm, [r'Bc1', r'Bd2', r'Be3', r'Bf4', r'Bg5', r'Bh6'], 30)
    if not dsb_moves and total > 20:
        ann['post'] = ann.get('post', '') + " The dark-squared bishop never developed — happens in 51% of Aman's White SW games. The DSB is the Stonewall's eternal problem."

    # Castling
    oo = has_move(wm, r'O-O', 15)
    if oo:
        ann[f'{oo}.w'] = f"Castles kingside (Aman's avg: move 8)."


def _ann_sw_black(ann, wm, bm, total):
    d5 = has_move(bm, r'd5', 5)
    e6 = has_move(bm, r'e6', 5)
    f5 = has_move(bm, r'f5', 15)
    bd6 = has_move(bm, r'Bd6', 10)

    if f5:
        ann[f'{f5}.b'] = "f5 — completing the Black Stonewall wall (d5+e6+f5). Structure locked in."
    if bd6:
        ann[f'{bd6}.b'] = "Bd6 — challenging White's dark-squared bishop if Bf4 was played. Key anti-London idea."

    ne4 = has_move(bm, r'Ne4', 20)
    if ne4:
        ann[f'{ne4}.b'] = f"Ne4! THE primary Black Stonewall plan (81% of Aman's games, avg move 11). The knight is untouchable on e4."

    # Pawns before pieces check
    first_piece = 999
    for n, m in bm:
        if n > 10:
            break
        if m[0] in 'NBRQK' and not m.startswith('O'):
            first_piece = n
            break
    pawn_count = sum(1 for n, m in bm if n < first_piece and n <= 10 and m[0].islower())
    if pawn_count >= 4:
        ann[f'{first_piece}.b'] = ann.get(f'{first_piece}.b', '') + f" First piece move after {pawn_count} pawn moves — Aman plays 4+ pawns first in 76% of Black SW games."

    # LSB maneuver
    bd7 = has_move(bm, r'Bd7', 15)
    be8 = has_move(bm, r'Be8', 25)
    bh5 = has_move(bm, r'Bh5', 30)
    if bd7 and be8:
        ann[f'{be8}.b'] = "Be8! LSB maneuver (Bd7→Be8→Bh5) — activating the 'bad' bishop."
    if bh5:
        ann[f'{bh5}.b'] = "Bh5! LSB reaches its ideal diagonal. The maneuver is complete."

    # Qe8 reroute
    qe8 = has_move(bm, r'Qe8', 20)
    if qe8:
        ann[f'{qe8}.b'] = "Qe8 — rerouting the queen, often heading to h5 or supporting kingside play."

    # Anti-London
    obf4 = has_move(wm, r'Bf4', 10)
    if obf4 and bd6:
        ann[f'{bd6}.b'] = "Bd6! Challenging Bf4 directly — the anti-London Stonewall approach."

    # Castling
    oo = has_move(bm, r'O-O', 15)
    if oo:
        ann[f'{oo}.b'] = f"Castles kingside (Aman's avg: move 8, KS 95%)."


# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER TITLES
# ═══════════════════════════════════════════════════════════════════════════════

def generate_chapter_title(variation, wm, bm, total_moves, player_color, opponent, termination):
    """Generate a descriptive chapter title like the lichess study format:
    (key features) Player - Opponent
    """
    is_black = player_color == 'black'
    pm = bm if is_black else wm
    om = wm if is_black else bm
    features = []

    # Variation is always first
    features.append(variation)

    # === FRENCH-SPECIFIC FEATURES ===

    # LSB solutions
    if is_black:
        if has_move(bm, r'Ba6', 25):
            features.append('Ba6 LSB trade')
        elif has_move(bm, r'Bg4', 15):
            features.append('Bg4 LSB activation')
        elif has_move(bm, r'Bf5', 15):
            features.append('Bf5 LSB activation')
        elif has_move(bm, r'Be6', 15):
            features.append('Be6 LSB')

        # Bd7-Bb5 maneuver
        if has_move(bm, r'Bd7', 15) and has_move(bm, r'Bb5', 25):
            features.append('Bd7-Bb5 maneuver')

    # Castling choice
    ooo = has_move(pm, r'O-O-O', 25)
    oo = has_move(pm, r'O-O', 25)
    if ooo:
        features.append('O-O-O')
    elif not oo and total_moves > 25:
        features.append('no castle')

    # Key tactical/strategic themes
    if is_black:
        if has_move(bm, r'Qb6', 15):
            features.append('Qb6 pressure')
        if has_move(bm, r'Qxb2', 30):
            features.append('b2 grab')
        if has_move(bm, r'Ne4', 20):
            features.append('Ne4 outpost')
        if has_move(bm, r'Bxc3', 10):
            features.append('Bxc3 doubled pawns')
        if has_move(bm, r'gxf6', 10):
            features.append('gxf6 bishop pair')
        if has_move(bm, r'dxe4', 10) and variation == 'Classical':
            features.append('Burn')

        # Nxa6-Nb8-Nc6 reroute (Winawer)
        if has_move(bm, r'Nxa6', 25) and has_move(bm, r'Nb8', 30):
            features.append('N reroute')

        # f5 or f6 break
        if has_move(bm, r'f6', 25):
            features.append('f6 break')
        elif has_move(bm, r'f5', 25):
            if variation == 'Exchange':
                features.append('SW attempt')
            else:
                features.append('f5 break')

        # Pawn storm
        if ooo and (has_move(bm, r'g5', 30) or has_move(bm, r'h5', 30)):
            features.append('pawn storm')

    else:  # White player
        if has_move(wm, r'Ne5', 20):
            features.append('Ne5')
        if has_move(wm, r'Bxh7', 30):
            features.append('Bxh7+ sac')
        if has_move(wm, r'g4', 25):
            features.append('g4 storm')
        if has_move(wm, r'e4', 25):
            features.append('e4 break')

    # Opponent disruptions
    if is_black:
        if has_move(wm, r'Bg5', 15):
            features.append('vs Bg5')
        if has_move(wm, r'Qe2', 10):
            features.append('vs Qe2')
        if has_move(wm, r'Qg4', 10):
            features.append('vs Qg4')

    # Game length / endgame
    if total_moves >= 50:
        features.append('long endgame')
    elif total_moves <= 25:
        features.append('quick win')

    # Termination
    if 'checkmate' in termination.lower() or 'mate' in termination.lower():
        features.append('checkmate')
    elif 'time' in termination.lower():
        features.append('time win')

    # Build title: (features) White - Black
    feature_str = ', '.join(features[:5])  # cap at 5 features to keep readable
    return f"({feature_str})"


# ═══════════════════════════════════════════════════════════════════════════════
# PGN OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

def build_pgn(headers, moves_raw, variation, opening, annotations, chapter_title=''):
    """Build clean annotated PGN for lichess import."""
    wm, bm = parse_chessdotcom_moves(moves_raw)
    result = headers.get('Result', '*')

    white_name = headers.get('White', '?')
    black_name = headers.get('Black', '?')

    out = []
    out.append(f'[Event "{chapter_title} {white_name} - {black_name}"]')
    out.append(f'[Site "{headers.get("Site", "Chess.com")}"]')
    out.append(f'[Date "{headers.get("Date", "????.??.??")}"]')
    out.append(f'[White "{headers.get("White", "?")}"]')
    out.append(f'[Black "{headers.get("Black", "?")}"]')
    out.append(f'[Result "{result}"]')
    for k in ('WhiteElo', 'BlackElo', 'ECO', 'Link'):
        if k in headers:
            out.append(f'[{k} "{headers[k]}"]')
    out.append('')

    # Build move text
    parts = []
    if 'pre' in annotations:
        parts.append(f'{{ {annotations["pre"]} }}')

    wd = {n: m for n, m in wm}
    bd = {n: m for n, m in bm}
    max_move = max([n for n, _ in wm] + [n for n, _ in bm]) if wm or bm else 0

    for i in range(1, max_move + 1):
        w = wd.get(i)
        b = bd.get(i)
        if w:
            parts.append(f'{i}. {w}')
            if f'{i}.w' in annotations:
                parts.append(f'{{ {annotations[f"{i}.w"]} }}')
        if b:
            if f'{i}.w' in annotations:
                parts.append(f'{i}... {b}')
            else:
                parts.append(b)
            if f'{i}.b' in annotations:
                parts.append(f'{{ {annotations[f"{i}.b"]} }}')

    if 'post' in annotations:
        parts.append(f'{{ {annotations["post"]} }}')
    parts.append(result)

    text = ' '.join(parts)
    lines = []
    cur = ''
    for word in text.split():
        if len(cur) + len(word) + 1 > 80 and cur:
            lines.append(cur)
            cur = word
        else:
            cur = cur + ' ' + word if cur else word
    if cur:
        lines.append(cur)

    return '\n'.join(out) + '\n' + '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Build chess opening study PGN')
    parser.add_argument('username', help='chess.com username')
    parser.add_argument('opening', choices=['french', 'stonewall'], help='Opening to extract')
    parser.add_argument('--max', type=int, default=64, help='Max games')
    parser.add_argument('--min-moves', type=int, default=20, help='Min game length')
    parser.add_argument('--pgn-path', help='Path to PGN file')
    args = parser.parse_args()

    username = args.username.lower()
    opening = args.opening

    # Find PGN
    pgn_path = args.pgn_path
    if not pgn_path:
        candidates = [
            os.path.join(WORKSPACE, 'opponents', username, 'games.pgn'),
            os.path.join(WORKSPACE, username, 'games.pgn'),
        ]
        for c in candidates:
            if os.path.exists(c):
                pgn_path = c
                break
    if not pgn_path or not os.path.exists(pgn_path):
        print(f"ERROR: No PGN found for {username}. Download first with:")
        print(f"  python3 skills/chess-opponent-scout/scripts/analyze_player.py {username} opponents/{username}")
        sys.exit(1)

    print(f"Reading {pgn_path}...")
    with open(pgn_path) as f:
        content = f.read()

    raw_games = re.split(r'\n(?=\[Event )', content)
    print(f"Total games in PGN: {len(raw_games)}")

    # Find qualifying games
    qualifying = []
    for raw in raw_games:
        headers = {}
        for m in re.finditer(r'\[(\w+) "([^"]*)"\]', raw):
            headers[m.group(1)] = m.group(2)

        white = headers.get('White', '').lower()
        black = headers.get('Black', '').lower()
        result = headers.get('Result', '')

        # Determine player color
        if username in white.lower():
            player_color = 'white'
            won = result == '1-0'
        elif username in black.lower():
            player_color = 'black'
            won = result == '0-1'
        else:
            continue

        if not won:
            continue

        parts = raw.split('\n\n', 1)
        if len(parts) < 2:
            continue
        moves_raw = parts[-1].strip()

        wm, bm = parse_chessdotcom_moves(moves_raw)
        if not wm:
            continue

        total = max([n for n, _ in wm] + [n for n, _ in bm]) if wm and bm else 0
        if total < args.min_moves:
            continue

        # Opening detection
        if opening == 'french':
            if not is_french(wm, bm, player_color):
                continue
            variation = classify_french(wm, bm)
        else:  # stonewall
            if not is_stonewall(wm, bm, player_color):
                continue
            variation = classify_stonewall(wm, bm, player_color)

        opponent = headers.get('White' if player_color == 'black' else 'Black', '?')
        opp_elo = int(headers.get('WhiteElo' if player_color == 'black' else 'BlackElo', '0'))

        headers['_player_color'] = player_color

        qualifying.append({
            'headers': headers,
            'moves_raw': moves_raw,
            'wm': wm,
            'bm': bm,
            'total_moves': total,
            'variation': variation,
            'player_color': player_color,
            'opponent': opponent,
            'opp_elo': opp_elo,
            'termination': headers.get('Termination', ''),
        })

    # Sort by opponent elo descending
    qualifying.sort(key=lambda x: -x['opp_elo'])

    print(f"\nQualifying {opening} wins: {len(qualifying)}")
    if not qualifying:
        print("No qualifying games found.")
        sys.exit(0)

    var_counts = Counter(g['variation'] for g in qualifying)
    print("Variation breakdown:")
    for v, c in var_counts.most_common():
        print(f"  {v}: {c}")

    # Annotate and build PGNs
    study_games = []
    for i, game in enumerate(qualifying[:args.max]):
        v = game['variation']
        if opening == 'french':
            annotations = annotate_french(
                v, game['wm'], game['bm'], game['total_moves'],
                username, game['opponent'], game['opp_elo'], game['player_color']
            )
        else:
            annotations = annotate_stonewall(
                v, game['wm'], game['bm'], game['total_moves'],
                username, game['opponent'], game['opp_elo'], game['player_color']
            )

        ann_count = sum(1 for k in annotations if k not in ('pre', 'post'))

        chapter_title = generate_chapter_title(
            v, game['wm'], game['bm'], game['total_moves'],
            game['player_color'], game['opponent'], game['termination']
        )

        pgn = build_pgn(game['headers'], game['moves_raw'], v, opening, annotations, chapter_title)
        study_games.append(pgn)

        print(f"[{i+1:2d}] {chapter_title[:60]:60s} | {game['total_moves']:3d}m | {ann_count} ann")

    # Write output
    out_dir = os.path.join(WORKSPACE, 'opponents', username)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'{username}-{opening}-study.pgn')

    with open(out_path, 'w') as f:
        f.write('\n\n'.join(study_games) + '\n')

    size = os.path.getsize(out_path)
    print(f"\nWrote {len(study_games)} games to {out_path} ({size:,} bytes)")

    # Summary
    elos = [g['opp_elo'] for g in qualifying[:args.max] if g['opp_elo'] > 0]
    if elos:
        print(f"Opponent rating range: {min(elos)}–{max(elos)} (avg {sum(elos)//len(elos)})")


if __name__ == '__main__':
    main()
