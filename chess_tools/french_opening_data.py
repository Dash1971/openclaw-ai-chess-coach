#!/usr/bin/env python3
"""French Defense opening-specific defaults and metadata.

Path defaults are intentionally cwd-relative (or /tmp for scratch files) so
that the public repo does not assume a built-in corpus or write derived files
into the source tree.  Supply explicit paths via CLI flags or environment
variables (OPENING_PGN_PATH, OPENING_TAG_OUTPUT, OPENING_GUIDE_OUTPUT).
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_PGN = Path('games.pgn')           # resolved against cwd at runtime
DEFAULT_TAG_OUTPUT = Path('/tmp/french_data.json')
DEFAULT_GUIDE_HTML = Path('/tmp/french_cheatsheet.html')
DEFAULT_GUIDE_PDF = Path('french-cheatsheet.pdf')  # resolved against cwd
MOVE_CUTOFF = 15

VARIATION_THEME_GROUPS = [
    ('var_exchange', 'Exchange Variation', 'All exchange games (3.exd5 exd5).'),
    ('var_advanced', 'Advanced Variation', 'All advanced games (3.e5).'),
    ('var_winawer_advanced', 'Winawer Advanced', 'Winawer into advanced pawn structure.'),
    ('var_winawer_exchange', 'Winawer Exchange', 'Winawer into exchange pawn structure.'),
    ('var_winawer_ne2_gambit', 'Winawer Ne2 Gambit', 'Unusual 4.Ne2 in the Winawer.'),
    ('var_winawer_transposition', 'Winawer Transposition', 'Winawer arising from non-standard move orders.'),
    ('var_tarrasch', 'Tarrasch', '3.Nd2 variation.'),
    ('var_kia', "KIA / King's Indian Attack", 'g3 setup from White.'),
    ('var_other', 'Other Sidelines', 'Non-standard White responses (2.Nf3, 2.f4, 2.Nc3, 2.c4, etc.).'),
]

EXCHANGE_THEME_GROUPS = [
    ('exchange_aggressive', 'Aggressive Exchange (O-O-O)', 'The attacking setup: Bd6 + LSB + Qd7 + O-O-O + pawn storm.'),
    ('exchange_conservative', 'Conservative Exchange (O-O)', 'The solid setup: Bd6 + c6 + Nf6 + O-O. Safe fallback.'),
    ('cons_re8_file', 'Conservative: Re8 Open File', 'Re8 seizing the open e-file — the primary active idea.'),
    ('cons_qc7_battery', 'Conservative: Qc7 Battery', 'Qc7 creating a battery with Bd6 toward h2.'),
    ('cons_qs_expansion', 'Conservative: QS Pawn Expansion', 'b5/a5 push — queenside space and targets.'),
    ('sw_reference', 'Stonewall References', 'Games where the SW was discussed, attempted, or avoided.'),
    ('opp_qe2_check', 'vs Qe2+ Disruption', 'Early queen check forces plan change.'),
]

STRATEGIC_THEME_GROUPS = [
    ('lsb_ba6_trade', 'LSB Trade via Ba6', 'b6 + Ba6 to trade the bad French bishop.'),
    ('lsb_developed', 'LSB Actively Developed', 'LSB to Bg4, Bf5, or Be6.'),
    ('knight_vs_bishop_endgame', 'Knight vs Bad Bishop Endgame', 'Games steering toward favorable N vs B endings.'),
    ('bishop_pair_advantage', 'Bishop Pair Advantage', 'Games where the bishop pair was a key factor.'),
    ('d4_pressure', 'Qb6 + Nc6 on d4', 'Combined pressure on the d4 pawn chain.'),
    ('b2_grab', 'b2 Pawn Grabs', 'Opponent blunders b2 after moving DSB.'),
    ('pawn_storm', 'Kingside Pawn Storm (O-O-O)', 'g5/h5 pawn storm after queenside castling.'),
    ('f6_control', 'f6 — E5/G5 Control', 'f6 controls key squares and prepares expansion.'),
    ('h6_snork', 'h6 Snork (Luft)', 'The classic safety move and Building Habits favorite.'),
    ('c5_break', 'c5 Pawn Break', 'Key lever in the advanced/Tarrasch.'),
    ('quick_win', 'Quick Wins (≤20 moves)', 'Games that ended fast.'),
]

DISRUPTION_THEME_GROUPS = [
    ('opp_nc3', 'Opponent Nc3', 'Knight attacks d5 — the most common disruption.'),
    ('opp_bg5_pin', 'Opponent Bg5 Pin', 'Bishop pins our knight. Answered with f6.'),
    ('opp_queen_check', 'Opponent Queen Check (Qe2+/Qh5+)', 'Early queen check disrupts plans.'),
    ('opp_c4', 'Opponent c4', 'Attacks our d5 pawn — kills the SW.'),
    ('opp_re1_check', 'Opponent Re1+', 'Rook check on the open e-file.'),
    ('opp_h3_tempo', 'Opponent h3 (Tempo Waste)', 'Wasted tempo — may enable the Stonewall.'),
]
