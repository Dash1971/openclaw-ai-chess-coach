#!/usr/bin/env python3
"""Stonewall opening-specific defaults and metadata.

Path defaults are intentionally cwd-relative (or /tmp for scratch files) so
that the public repo does not assume a built-in corpus or write derived files
into the source tree.  Supply explicit paths via CLI flags or environment
variables (OPENING_PGN_PATH, OPENING_TAG_OUTPUT, OPENING_GUIDE_OUTPUT).
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_PGN = Path('games.pgn')           # resolved against cwd at runtime
DEFAULT_TAG_OUTPUT = Path('/tmp/sw_data.json')
DEFAULT_GUIDE_HTML = Path('/tmp/stonewall_cheatsheet.html')
DEFAULT_GUIDE_PDF = Path('stonewall-cheatsheet.pdf')  # resolved against cwd
MOVE_CUTOFF = 15

WHITE_ATTACK_THEMES = [
    ('ne5', 'Ne5 Outpost', 'The primary weapon — knight on e5 attacking f7 and supporting the attack.'),
    ('ne5_before_castle', 'Ne5 Before Castling', 'Games where Ne5 was played before O-O — see Section 5 for full breakdown.'),
    ('g4_storm', 'g4 Kingside Storm (all types)', 'All games featuring the g4 push regardless of trigger.'),
    ('e4_break', 'e4 Central Break (all)', 'All games featuring the thematic e4 pawn break — see Section 6.'),
    ('e4_after_c4', "e4 After Opponent's ...c4", 'Strongest trigger: opponent locks QS with ...c4, freeing our e-pawn.'),
    ('e4_ne5_on_board', 'e4 With Ne5 On Board', 'Plan B: Ne5 unchallenged, e4 opens the position while knight dominates.'),
    ('e4_vs_kid', 'e4 vs KID/Passive Setups', 'e4 seizes space against fianchetto/passive opponents.'),
    ('e4_lsb_traded', 'e4 After LSB Traded', 'LSB exchanged — e4 compensates by opening lines for remaining pieces.'),
    ('bxh7_sac', 'Bxh7+ Greek Gift (True Sacrifice)', 'Unsupported LSB sacrifice on h7 to expose the king.'),
    ('bxh7_supported', 'Bxh7 Supported Capture', 'Bxh7 with rook/queen already on h-file.'),
    ('bxh6_attack', 'Bxh6 DSB Kingside Attack', 'DSB captures h6 pawn — rips open kingside shelter.'),
    ('rxf3_sac', 'Rxf3 / Exchange Sac Motif', 'Rook sac on f3 once the h-file and bishop diagonals are primed.'),
    ('qf3', 'Qf3 Attack Setup', 'Queen to f3 — defends e4, supports g4, eyes the kingside.'),
    ('queen_guard_e4', 'Queen Guarding LSB / e4', 'Qc2, Qe1, or Qe2 used to hold e4 and keep the LSB healthy.'),
    ('bc2_battery', 'Bc2 Battery', 'Bishop retreats to c2 creating a battery with the queen.'),
    ('quick_win', 'Quick Wins (≤20 moves)', 'Games that ended fast — the Stonewall can be a quick killer.'),
]

WHITE_STRUCTURAL_THEMES = [
    ('dsb_maneuver', 'DSB Maneuver (all types)', 'All games featuring Bd2→Be1(→Bh4) regardless of trigger.'),
    ('dsb_vs_symmetrical', 'DSB Maneuver vs Symmetrical SW', 'Triggered when opponent plays ...f5.'),
    ('dsb_vs_kid', 'DSB Maneuver vs KID / Indian Setups', 'Triggered when opponent has uncommitted center (no ...d5).'),
    ('nd2_first', 'Nd2 Before Nf3', 'Aman prioritizes Nd2 to prevent ...Nd4.'),
    ('nd2_futile_symmetrical', 'Nd2 Futile vs Symmetrical SW', 'Symmetrical structure means Nd2 alone does not solve ...Ne4.'),
    ('vs_symmetrical', 'vs Symmetrical / Dutch SW', 'All games where opponent plays ...f5.'),
    ('vs_fianchetto', 'vs Fianchetto Setups', 'Opponent fianchettoes kingside.'),
    ('early_f4_bg4', 'Early f4 vs ...Bg4', 'f4 played early to keep Nf3 available against ...Bg4.'),
]

WHITE_THREAT_THEMES = [
    ('opp_qb6', 'vs ...Qb6 Pin', 'Opponent pins the d4 pawn — dangerous after exd4.'),
    ('opp_bb7', 'vs ...Bb7 Fianchetto', 'Opponent threatens to force Ne4 via the b7 bishop.'),
    ('opp_bd6_c5', 'vs ...Bd6 + ...c5', 'Threatens f-pawn weakness after pawn exchanges.'),
    ('opp_ba6_trade', 'vs Ba6 Forced Trade', 'Opponent pushes a/b pawns to force a bishop trade.'),
]

BLACK_THEMES = [
    ('ne4', 'Ne4 Outpost', "The backbone of Black's middlegame — knight on e4."),
    ('ne4_before_castle', 'Ne4 Before Castling', 'Games where Ne4 was played before O-O — see Section 5 for full breakdown. Perfect record.'),
    ('lsb_maneuver', 'LSB Maneuver (all types)', 'Bd7→Be8→Bh5 — activating the bad light-squared bishop.'),
    ('lsb_vs_symmetrical', 'LSB vs Symmetrical SW', 'Triggered when opponent plays f4.'),
    ('lsb_vs_kia', 'LSB vs KIA / Indian Setups', "Mirror of White's DSB vs KID. Triggered when opponent has uncommitted center."),
    ('e5_break', '...e5 Central Break', "Black's central pawn break — rarer than White's e4 but it exists."),
    ('g5_push', '...g5 Kingside Push', "The aggressive pawn advance — mirror of White's g4."),
    ('bxh2_attack', 'Bxh2+ Attack', "Mirror of White's Bxh7+ — DSB attacks h2."),
    ('quick_win', 'Quick Wins (≤20 moves)', 'Games that ended fast.'),
    ('queen_reroute', 'Queen Reroute (Qe8/Qe7)', 'Queen repositioned for kingside attack.'),
    ('nd7_prophylaxis', '...Nd7 to Stop Ne5', 'Black uses ...Nd7 prophylactically — but only when the structure supports it.'),
    ('early_bd6_london', 'Early ...Bd6 vs London', 'Breaking the "pawns first" rule to challenge Bf4.'),
    ('opp_ne5', 'Opponent Plays Ne5', "How Aman handles the opponent's knight outpost."),
]

BLACK_OPENING_THEMES = [
    ('vs_e4', 'vs 1.e4 — French Stonewall', 'Stonewall arising from the French Defence.'),
    ('vs_london', 'vs London System (Bf4)', 'Includes early ...Bd6 to challenge the London bishop.'),
    ('vs_d4_c4', 'vs 1.d4 + c4 Systems', 'Opponent plays c4 challenging the d5 pawn.'),
    ('vs_d4_other', 'vs 1.d4 (other)', 'Non-London, non-c4 d4 openings.'),
    ('full_wall', 'Full Pawn Wall Achieved', 'All four wall pawns (d5+e6+f5+c6) established.'),
]

