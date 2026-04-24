#!/usr/bin/env python3
"""Generate Stonewall Cheat Sheet PDF from tagged game data.

Prerequisites: Run tag_games.py (or tag_opening.py stonewall) first to
produce the JSON input (default: /tmp/sw_data.json).

Usage:
    python3 generate_pdf.py
    OPENING_GUIDE_INPUT=/path/to/data.json OPENING_GUIDE_OUTPUT=out.pdf python3 generate_pdf.py


ANTI-REGRESSION RULES:
- Do not hardcode living-corpus percentages in prose. If the DB changes, compute both counts and percentages from current data.
- Do not mix live counts with stale literal percentages.
- Keep White-only and Black-only timing/plan notes on the correct side unless the opposite-side claim is directly supported by notes/games.
"""

import json
import os
import chess
import chess.svg
from datetime import datetime
from diagram_helpers import diagram_html, DIAGRAM_CSS
from opening_guide_pipeline import load_guide_data, write_guide_outputs
from opening_guide_utils import build_game_link, game_list_html as shared_game_list_html, theme_box as shared_theme_box
from stonewall_opening_data import (
    BLACK_OPENING_THEMES,
    BLACK_THEMES,
    DEFAULT_GUIDE_HTML,
    DEFAULT_GUIDE_PDF,
    DEFAULT_TAG_OUTPUT,
    WHITE_ATTACK_THEMES,
    WHITE_STRUCTURAL_THEMES,
    WHITE_THREAT_THEMES,
)

INPUT_JSON = os.environ.get('OPENING_GUIDE_INPUT', str(DEFAULT_TAG_OUTPUT))
HTML_DEBUG = os.environ.get('OPENING_GUIDE_HTML', str(DEFAULT_GUIDE_HTML))

data = load_guide_data(INPUT_JSON)

white_games = data['white_games']
black_games = data['black_games']


def game_link(g, is_white=True):
    """Generate a clickable game link."""
    return build_game_link(g, opponent_field='black' if is_white else 'white')


def game_list_html(games, is_white=True, columns=2):
    """Generate a UL game list."""
    return shared_game_list_html(games, lambda g: game_link(g, is_white), columns=columns)


def theme_box(title, description, games, is_white=True, columns=2):
    """Generate a themed game section."""
    return shared_theme_box(title, description, games, lambda g: game_link(g, is_white), columns=columns)


def tagged(games, tag):
    """Filter games by tag."""
    return [g for g in games if tag in g.get('tags', [])]


# Count helpers
n_white = len(white_games)
n_black = len(black_games)
today = datetime.now().strftime("%B %d, %Y")

# ============================================================
# Build HTML
# ============================================================
html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
    size: A4;
    margin: 18mm 15mm 18mm 15mm;
    @bottom-center {{
        content: counter(page);
        font-size: 9px;
        color: #999;
    }}
}}

body {{
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 10.5px;
    line-height: 1.5;
    color: #1a1a1a;
}}

h1 {{
    font-size: 24px;
    text-align: center;
    margin: 0 0 4px 0;
    color: #1a1a1a;
    letter-spacing: -0.5px;
}}

.subtitle {{
    text-align: center;
    color: #666;
    font-size: 11px;
    margin: 0 0 20px 0;
}}

h2 {{
    font-size: 16px;
    color: #fff;
    padding: 8px 14px;
    margin: 22px 0 12px 0;
    border-radius: 4px;
    page-break-after: avoid;
}}

h2.white-section {{ background: #2c3e50; }}
h2.black-section {{ background: #1a1a2e; }}
h2.compare-section {{ background: #4a1942; }}
h2.stats-section {{ background: #0d4f2b; }}
h2.themes-section {{ background: #7f4b1e; }}
h2.threats-section {{ background: #8b1a1a; }}

h3 {{
    font-size: 13px;
    color: #2c3e50;
    margin: 14px 0 6px 0;
    border-bottom: 1.5px solid #e0e0e0;
    padding-bottom: 3px;
    page-break-after: avoid;
}}

h4 {{
    font-size: 11px;
    color: #444;
    margin: 10px 0 4px 0;
    page-break-after: avoid;
}}

p {{ margin: 4px 0; }}

.overview-box {{
    background: #f8f9fa;
    border-left: 4px solid #2c3e50;
    padding: 10px 14px;
    margin: 8px 0;
    border-radius: 0 4px 4px 0;
}}

.overview-box.black {{ border-left-color: #1a1a2e; }}

.heuristic {{
    background: #fff3cd;
    border: 1px solid #ffc107;
    padding: 8px 12px;
    margin: 8px 0;
    border-radius: 4px;
    font-size: 10.5px;
}}

.heuristic strong {{ color: #856404; }}

.insight {{
    background: #d4edda;
    border: 1px solid #28a745;
    padding: 8px 12px;
    margin: 8px 0;
    border-radius: 4px;
}}

.insight strong {{ color: #155724; }}

.surprise {{
    background: #f8d7da;
    border: 1px solid #dc3545;
    padding: 8px 12px;
    margin: 8px 0;
    border-radius: 4px;
}}

.surprise strong {{ color: #721c24; }}

.mirror-box {{
    background: #e8eaf6;
    border: 1px solid #5c6bc0;
    padding: 8px 12px;
    margin: 8px 0;
    border-radius: 4px;
}}

.mirror-box strong {{ color: #283593; }}

.stat-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 10px;
}}

.stat-table th {{
    background: #f0f0f0;
    padding: 5px 8px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #ccc;
}}

.stat-table td {{
    padding: 4px 8px;
    border-bottom: 1px solid #eee;
}}

.stat-table tr:nth-child(even) {{ background: #fafafa; }}

.move-order {{
    font-family: 'Courier New', monospace;
    font-size: 10px;
    background: #f5f5f5;
    padding: 6px 10px;
    border-radius: 3px;
    margin: 4px 0;
}}

.theme-group {{
    margin: 6px 0;
    page-break-inside: avoid;
}}

.theme-desc {{
    font-size: 9.5px;
    color: #555;
    font-style: italic;
    margin: 2px 0 4px 0;
}}

.game-list {{
    margin: 2px 0;
    padding-left: 18px;
    font-size: 9.5px;
    column-gap: 20px;
}}

.game-list li {{
    margin: 1px 0;
    break-inside: avoid;
}}

.count {{
    color: #888;
    font-weight: normal;
    font-size: 10px;
}}

.theme-hint {{
    color: #999;
    font-size: 8.5px;
    font-style: italic;
}}

a {{ color: #2980b9; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

.toc {{
    background: #f8f9fa;
    padding: 12px 18px;
    border-radius: 6px;
    margin: 12px 0;
}}

.toc ol {{ margin: 4px 0; padding-left: 20px; }}
.toc li {{ margin: 3px 0; font-size: 11px; }}
.toc .sub {{ margin-left: 20px; font-size: 10px; color: #555; }}

.key-stat {{
    display: inline-block;
    background: #e8f4fd;
    border: 1px solid #bee5eb;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 10px;
    margin: 2px 1px;
    white-space: nowrap;
}}

.empty {{ color: #999; font-style: italic; font-size: 9.5px; }}

{DIAGRAM_CSS}
</style>
</head>
<body>

<h1>The Stonewall Playbook</h1>
<p class="subtitle">A Data-Driven Cheat Sheet from {n_white} White + {n_black} Black Games<br>
Based on Aman Hambleton's (wonestall) Stonewall Speedrun &bull; Generated {today}</p>

<div class="toc">
<strong>Contents</strong>
<ol>
<li>White Stonewall — Overview, Plans & Key Ideas</li>
<li>Black Stonewall — Overview, Plans & Key Ideas</li>
<li>White vs Black — Same System, Different Philosophy</li>
<li>Statistics Deep Dive — Numbers That Tell Stories</li>
<li>Ne5/Ne4 Before Castling — When to Delay Castling</li>
<li>The e4 Central Break — Triggers, Plans & Timing</li>
<li>The g4 Kingside Storm — When, Why & How</li>
<li>The Bad Bishop Maneuver — DSB (White) & LSB (Black)</li>
<li>Bishop Attacks on the Kingside (Bxh7+ & Bxh6)</li>
<li>Opponent Threats & How to Handle Them</li>
<li>Games by Theme — Clickable Study Links</li>
</ol>
</div>

<!-- ============================================================ -->
<h2 class="white-section">1. White Stonewall — The Attacker's System</h2>
<!-- ============================================================ -->

<h3>The Structure</h3>
<div class="overview-box">
<p><strong>Pawns:</strong> d4 + e3 + f4 (+ c3 when needed). The f4 pawn is the signature — it stakes a claim on the kingside and prepares the attack.</p>
<p><strong>Key piece:</strong> Bishop on d3, aimed at the h7 pawn. This is the cannon. Everything else supports it.</p>
<p><strong>The deal:</strong> You accept a "bad" dark-squared bishop (blocked by e3/f4) in exchange for a clear attacking plan against the enemy king.</p>
</div>

{diagram_html(
    'r1bq1rk1/ppp1bppp/2n1pn2/3pN3/3P1P2/2PBP3/PP1N2PP/R1BQ1RK1 w - - 0 10',
    'The ideal White Stonewall: c3+d4+e3+f4 wall, Bd3 cannon aimed at h7, Ne5 dominating the center, Nd2 protecting d4.',
    arrows=[chess.svg.Arrow(chess.D3, chess.H7, color='#ff0000aa')]
)}

<h3>The Opening Recipe</h3>
<div class="move-order">
<strong>The Core (almost every game):</strong> 1.d4 → 2.e3 (96%) → 3.Bd3 (62%) or 3.f4 (23%)<br>
<strong>Most common first 4:</strong> d4 e3 Bd3 f4 (34 games) &nbsp;|&nbsp; d4 e3 f4 Bd3 (17 games) &nbsp;|&nbsp; d4 e3 Bd3 Nd2 (14 games)
</div>

<div class="heuristic">
<strong>💡 Rule of Thumb:</strong> Always d4, always e3, always Bd3. The order of f4 and c3 depends on what your opponent does. If they're developing normally, get Bd3 out first (it's your most important piece). If they threaten ...c5 or ...e5 quickly, consider f4 or c3 earlier.
</div>

<h3>The Five Middlegame Plans</h3>

<p><strong>Plan A: The Ne5 Squeeze ({len(tagged(white_games, 'ne5'))} games, {len(tagged(white_games, 'ne5'))*100//max(1,n_white)}%)</strong><br>
Plant your knight on e5. From there it attacks f7, supports Qf3/Qh5, and controls key squares. Average move: ~11.</p>

<p><strong>Plan B: The g4 Storm ({len(tagged(white_games, 'g4_storm'))} games, {len(tagged(white_games, 'g4_storm'))*100//max(1,n_white)}%)</strong><br>
Push g4 to blast open the g-file. Often preceded by Qf3 and Rg1/Rf3. See <strong>Section 7</strong> for the full breakdown of when and how.</p>

<p><strong>Plan C: The e4 Break ({len(tagged(white_games, 'e4_break'))} games, {len(tagged(white_games, 'e4_break'))*100//max(1,n_white)}%)</strong><br>
The most reliable central break — 100% win rate. Push e3→e4 to open the center, free the DSB, and create tactical threats. See <strong>Section 6</strong> for the complete analysis with triggers, plans, and timing.</p>

<p><strong>Plan D: Bishop Attacks — Bxh7+ & Bxh6 ({len(tagged(white_games, 'bxh7_attack'))} + {len(tagged(white_games, 'bxh6_attack'))} games)</strong><br>
Two distinct bishop attacks: the LSB sacrifice on h7 (Greek Gift), and the DSB sacrifice on h6 (ripping open the kingside after ...h6). See <strong>Section 9</strong> for full breakdown.</p>

<p><strong>Plan E: The DSB Maneuver ({len(tagged(white_games, 'dsb_maneuver'))} games, {len(tagged(white_games, 'dsb_maneuver'))*100//max(1,n_white)}%)</strong><br>
Bd2→Be1→Bh4 to activate the "bad" bishop. See <strong>Section 8</strong> for triggers and when to use it.</p>

<div class="insight">
<strong>📊 Data Insight:</strong> Plans overlap heavily. A typical attacking game starts with Ne5, transitions to Qf3 or g4, and may finish with Bxh7+ or a breakthrough on the f-file. Think of them as a toolkit, not separate plans.
</div>

<h3>The Nd2 Priority</h3>
<p>Aman develops Nd2 in <strong>60 of {n_white} games</strong> (51%). In {len(tagged(white_games, 'nd2_first'))} games, Nd2 comes <em>before</em> Nf3.</p>

<div class="heuristic">
<strong>💡 Why Nd2?</strong> Prevents ...Nd4 (a monster in your camp). Also supports Ne5 transfers (Nd2→Nf3→Ne5). <strong>BUT:</strong> Against symmetrical SW structures (opponent plays ...f5), Nd2 is often futile because ...Ne4 is protected by the d5 and f5 pawns. In those positions, consider the DSB maneuver instead (Section 8). Playing Nd2 in a symmetrical SW can actually <em>block in</em> the DSB, making the maneuver impossible.
</div>

<div class="insight">
<strong>🔍 Quiet support move:</strong> In <strong>{len(tagged(white_games, 'queen_guard_e4'))} annotated games</strong>, White uses <strong>Qc2 / Qe1 / Qe2</strong> to do two jobs at once: guard the light-squared bishop and help hold the <strong>e4</strong> square / e-file before committing the knight structure. When Nd2 alone does not solve the square, the queen often does the hidden defensive work first.
</div>

<h3>Castling</h3>
<p><strong>Kingside: 95%</strong> of games. Average castling move: <strong>8.3</strong>.</p>

<!-- ============================================================ -->
<h2 class="black-section">2. Black Stonewall — The Fortress Builder</h2>
<!-- ============================================================ -->

<h3>The Structure</h3>
<div class="overview-box black">
<p><strong>Pawns:</strong> d5 + e6 + f5 + c6. Four pawns forming an unbreakable wall. The c6 pawn is more consistently part of the Black setup than c3 is for White.</p>
<p><strong>Key piece:</strong> Bishop on d6 (the "good" dark-squared bishop), aimed at the kingside.</p>
<p><strong>The problem piece:</strong> The light-squared bishop on c8 is trapped behind e6/d5/f5. Finding activity for this bishop is the central strategic challenge.</p>
</div>

{diagram_html(
    'r1bq1rk1/pp4pp/2pbp3/3p1p2/3Pn3/2N1BN2/PPP1BPPP/R2Q1RK1 b - - 0 10',
    'The ideal Black Stonewall: d5+e6+f5+c6 wall, Bd6 on the strong diagonal, Ne4 on the dream outpost. The c8 bishop is the problem piece — trapped behind the wall.',
    flipped=True
)}

<h3>The Opening Recipe</h3>

<p><strong>vs 1.d4 ({len(tagged(black_games, 'vs_london')) + len(tagged(black_games, 'vs_d4_c4')) + len(tagged(black_games, 'vs_d4_other'))} games):</strong></p>
<div class="move-order">
<strong>Standard:</strong> 1...d5 → 2...e6 → 3...c6 → 4...f5 (then Bd6, Nf6, O-O)<br>
<strong>Key principle:</strong> Pawns first, pieces second. In 62% of d4 games, 4+ pawns are placed before any piece.
</div>

<p><strong>vs 1.e4 ({len(tagged(black_games, 'vs_e4'))} games):</strong></p>
<div class="move-order">
<strong>French setup:</strong> 1...e6 → 2...d5 → then after exd5 exd5, play ...f5, ...Nf6, ...Bd6<br>
The Stonewall arises via a French Defence move order.
</div>

<div class="heuristic">
<strong>💡 Rule of Thumb (Black vs d4):</strong> Build the wall first: d5, e6, c6, f5 — usually in that order. Only after the wall is up do you develop pieces. The wall determines WHERE pieces belong.
</div>

<h3>The London Exception</h3>
<p>Against the London System (2.Bf4), Aman sometimes breaks the "pawns first" rule. In 3 games, <strong>Bd6 came before ...f5</strong> — challenging the Bf4 directly to prevent a dark-square bind.</p>

<h3>Middlegame Plans</h3>

<p><strong>Plan A: The Ne4 Outpost ({len(tagged(black_games, 'ne4'))} games, {len(tagged(black_games, 'ne4'))*100//max(1,n_black)}%)</strong><br>
The backbone of Black's middlegame. Plant a knight on e4, attacking d2/f2 and controlling key squares. Average move: ~11.</p>

<p><strong>Plan B: The LSB Maneuver ({len(tagged(black_games, 'lsb_maneuver'))} games)</strong><br>
Bd7→Be8→Bh5 to activate the bad bishop. See <strong>Section 8</strong> for when to deploy this vs Ne4.</p>

<p><strong>Plan C: Queen Reroute ({len(tagged(black_games, 'queen_reroute'))} games)</strong><br>
Swing the queen to e8, then potentially g6 or h5. Often combines with the LSB maneuver.</p>

<p><strong>Plan D: ...g5 Push ({len(tagged(black_games, 'g5_push'))} games)</strong><br>
The aggressive kingside pawn advance. Rare but powerful — this is the Black mirror of White's g4 storm.</p>

<p><strong>Plan E: Bxh2+ Sacrifice ({len(tagged(black_games, 'bxh2_attack'))} games)</strong><br>
The Black mirror of White's Bxh7+ Greek Gift — sacrificing the dark-squared bishop to expose White's king.</p>

<h3>Dealing with Ne5</h3>
<p>White played Ne5 in <strong>{len(tagged(black_games, 'opp_ne5'))} of {n_black} games ({len(tagged(black_games, 'opp_ne5'))*100//max(1,n_black)}%)</strong>. Aman's response: <em>ignore it and continue with the plan.</em> The pawn wall (d5-e6-f5-c6) is structurally sound regardless. Black's counterplay comes from Ne4 and the kingside, not from fighting for e5.</p>

<div class="heuristic">
<strong>💡 New black-side nuance:</strong> <strong>...Nd7</strong> is a tool, not a law. The refreshed notes show it used in <strong>{len(tagged(black_games, 'nd7_prophylaxis'))} games</strong> to stop Ne5, but later games often prefer castling, bishop activity, or a direct <strong>...Ne4</strong> plan instead. If ...Nd7 kills your c-pawn flexibility or points you toward an ugly <strong>...cxd5</strong> recapture, don't force it.
</div>

<h3>Castling</h3>
<p><strong>Kingside: 89%</strong>. Average move: <strong>8.2</strong> (close to White's 8.3).</p>

<!-- ============================================================ -->
<h2 class="compare-section">3. White vs Black — Same System, Different Philosophy</h2>
<!-- ============================================================ -->

<h3>What's the Same</h3>
<table class="stat-table">
<tr><th>Feature</th><th>White</th><th>Black</th></tr>
<tr><td>Core pawn chain</td><td>d4-e3-f4</td><td>d5-e6-f5</td></tr>
<tr><td>Average castling move</td><td>8.3</td><td>8.4</td></tr>
<tr><td>Knight outpost</td><td>Ne5 ({len(tagged(white_games, 'ne5'))*100//max(1,n_white)}%)</td><td>Ne4 ({len(tagged(black_games, 'ne4'))*100//max(1,n_black)}%)</td></tr>
<tr><td>Outpost timing</td><td>Move ~11</td><td>Move ~11</td></tr>
<tr><td>Bad bishop maneuver</td><td>DSB: Bd2→Be1→Bh4</td><td>LSB: Bd7→Be8→Bh5</td></tr>
<tr><td>Bishop attacks</td><td>Bxh7+ ({len(tagged(white_games, 'bxh7_attack'))*100//max(1,n_white)}%) + Bxh6 ({len(tagged(white_games, 'bxh6_attack'))*100//max(1,n_white)}%)</td><td>Bxh2+ (rare)</td></tr>
<tr><td>Central break</td><td>e4 ({len(tagged(white_games, 'e4_break'))*100//max(1,n_white)}%)</td><td>e5 ({len(tagged(black_games, 'e5_break'))*100//max(1,n_black)}%)</td></tr>
</table>

<h3>What's Different</h3>
<table class="stat-table">
<tr><th>Aspect</th><th>White</th><th>Black</th></tr>
<tr><td><strong>Opening priority</strong></td><td>Piece development (Bd3 by move 3)</td><td>Pawn structure (3-4 pawns before pieces)</td></tr>
<tr><td><strong>Bad bishop strategy</strong></td><td>Often leave DSB on c1 ({(n_white-len(tagged(white_games, 'dsb_maneuver')))*100//max(1,n_white)}% never moves). General-purpose maneuver.</td><td>LSB maneuver is more specialized — about {len(tagged(black_games, 'lsb_vs_symmetrical'))*100//max(1,len(tagged(black_games, 'lsb_maneuver')))}% of LSB maneuver games are triggered by symmetrical structures.</td></tr>
<tr><td><strong>Preventing infiltration</strong></td><td>Often uses Nd2 to prevent ...Nd4 (60 games total)</td><td>Tolerates Ne5 ({len(tagged(black_games, 'opp_ne5'))*100//max(1,n_black)}% of games)</td></tr>
<tr><td><strong>Kingside storm</strong></td><td>g4 ({len(tagged(white_games, 'g4_storm'))*100//max(1,n_white)}%) — multiple triggers</td><td>g5 ({len(tagged(black_games, 'g5_push'))*100//max(1,n_black)}%) — much rarer</td></tr>
</table>

<h3>The Mirror Patterns</h3>
<div class="mirror-box">
<strong>🪞 What transfers from White to Black:</strong>
<ul>
<li><strong>Bad bishop maneuver vs symmetrical positions</strong> — White DSB maneuver when opponent plays Dutch/SW; Black LSB maneuver when opponent plays f4. Same trigger, same logic.</li>
<li><strong>Bad bishop maneuver vs passive/Indian setups</strong> — White DSB maneuver vs KID (opponent doesn't commit central pawns to 4th rank, controls e5 from behind); Black LSB maneuver vs KIA (opponent plays g3, uncommitted center denies Ne4 support). Same logic: when the outpost is structurally denied, activate the bad bishop instead.</li>
<li><strong>Bishop sacrifice on the h-pawn</strong> — White Bxh7+ to expose Black's king; Black Bxh2+ to expose White's king. Same concept, different direction.</li>
<li><strong>Kingside pawn storm</strong> — g4 (White) and g5 (Black). Both look to blast open files against the enemy king.</li>
</ul>
<strong>🚫 What does NOT transfer:</strong>
<ul>
<li><strong>Nd2 urgency</strong> — White must prevent ...Nd4; Black tolerates Ne5 because the wall is structurally sound.</li>
<li><strong>g4 frequency</strong> — White pushes g4 in {len(tagged(white_games, 'g4_storm'))*100//max(1,n_white)}% of games; Black pushes g5 in only {len(tagged(black_games, 'g5_push'))*100//max(1,n_black)}%.</li>
<li><strong>e4/e5 break frequency</strong> — White has e4 ({len(tagged(white_games, 'e4_break'))*100//max(1,n_white)}%); Black has ...e5 but much rarer ({len(tagged(black_games, 'e5_break'))*100//max(1,n_black)}%).</li>
</ul>
</div>

<div class="heuristic">
<strong>White = Build the cannon (Bd3) first, then the fortress.</strong><br>
<strong>Black = Build the fortress (d5-e6-f5-c6) first, then find the cannon.</strong>
</div>

<!-- ============================================================ -->
<h2 class="stats-section">4. Statistics Deep Dive</h2>
<!-- ============================================================ -->

<h3>White Opening Move Order</h3>
<table class="stat-table">
<tr><th>Move</th><th>When Played</th><th>Frequency</th></tr>
<tr><td><strong>d4</strong></td><td>Always move 1</td><td>{n_white}/{n_white} (100%)</td></tr>
<tr><td><strong>e3</strong></td><td>Move 2 (97%), Move 3 (3%)</td><td>115/{n_white} (99%)</td></tr>
<tr><td><strong>Bd3</strong></td><td>Move 3 (72x), Move 4 (24x)</td><td>113/{n_white} (97%)</td></tr>
<tr><td><strong>f4</strong></td><td>Move 3-5 (most by move 5)</td><td>{n_white}/{n_white} (100%)</td></tr>
<tr><td><strong>c3</strong></td><td>Scattered (move 5-7)</td><td>104/{n_white} (89%)</td></tr>
<tr><td><strong>Nd2</strong></td><td>Move 4-8</td><td>60/{n_white} (51%)</td></tr>
<tr><td><strong>O-O</strong></td><td>Move 6-8</td><td>111/{n_white} (95%)</td></tr>
</table>

<div class="heuristic">
<strong>💡 New note-level pattern:</strong> early <strong>f4</strong> is often prophylaxis, not impatience. In <strong>{len(tagged(white_games, 'early_f4_bg4'))} annotated games</strong>, the point is specifically to keep <strong>Nf3</strong> available against <strong>...Bg4</strong>. White is buying piece freedom before the pin arrives.
</div>

<h3>Knight Outpost Comparison</h3>
<table class="stat-table">
<tr><th>Metric</th><th>White (Ne5)</th><th>Black (Ne4)</th></tr>
<tr><td>Games with outpost</td><td>{len(tagged(white_games, 'ne5'))}/{n_white} ({len(tagged(white_games, 'ne5'))*100//max(1,n_white)}%)</td><td>{len(tagged(black_games, 'ne4'))}/{n_black} ({len(tagged(black_games, 'ne4'))*100//max(1,n_black)}%)</td></tr>
<tr><td>Average timing</td><td>Move ~11</td><td>Move ~11</td></tr>
</table>

<h3>Attack Patterns (White)</h3>
<table class="stat-table">
<tr><th>Attack Type</th><th>Games</th><th>Rate</th></tr>
<tr><td>Ne5 outpost</td><td>{len(tagged(white_games, 'ne5'))}</td><td>{len(tagged(white_games, 'ne5'))*100//max(1,n_white)}%</td></tr>
<tr><td>g4 kingside storm</td><td>{len(tagged(white_games, 'g4_storm'))}</td><td>{len(tagged(white_games, 'g4_storm'))*100//max(1,n_white)}%</td></tr>
<tr><td>e4 central break</td><td>{len(tagged(white_games, 'e4_break'))}</td><td>{len(tagged(white_games, 'e4_break'))*100//max(1,n_white)}%</td></tr>
<tr><td>DSB maneuver</td><td>{len(tagged(white_games, 'dsb_maneuver'))}</td><td>{len(tagged(white_games, 'dsb_maneuver'))*100//max(1,n_white)}%</td></tr>
<tr><td>Qf3 setup</td><td>{len(tagged(white_games, 'qf3'))}</td><td>{len(tagged(white_games, 'qf3'))*100//max(1,n_white)}%</td></tr>
<tr><td>Bxh7+ Greek gift</td><td>{len(tagged(white_games, 'bxh7_attack'))}</td><td>{len(tagged(white_games, 'bxh7_attack'))*100//max(1,n_white)}%</td></tr>
<tr><td>Queen support (Qc2/Qe1/Qe2)</td><td>{len(tagged(white_games, 'queen_guard_e4'))}</td><td>{len(tagged(white_games, 'queen_guard_e4'))*100//max(1,n_white)}%</td></tr>
<tr><td>Rxf3 / exchange sac motif</td><td>{len(tagged(white_games, 'rxf3_sac'))}</td><td>{len(tagged(white_games, 'rxf3_sac'))*100//max(1,n_white)}%</td></tr>
<tr><td>Quick wins (≤20 moves)</td><td>{len(tagged(white_games, 'quick_win'))}</td><td>{len(tagged(white_games, 'quick_win'))*100//max(1,n_white)}%</td></tr>
</table>

<h3>Attack Patterns (Black)</h3>
<table class="stat-table">
<tr><th>Attack Type</th><th>Games</th><th>Rate</th></tr>
<tr><td>Ne4 outpost</td><td>{len(tagged(black_games, 'ne4'))}</td><td>{len(tagged(black_games, 'ne4'))*100//max(1,n_black)}%</td></tr>
<tr><td>Queen reroute (Qe8/Qe7)</td><td>{len(tagged(black_games, 'queen_reroute'))}</td><td>{len(tagged(black_games, 'queen_reroute'))*100//max(1,n_black)}%</td></tr>
<tr><td>LSB maneuver</td><td>{len(tagged(black_games, 'lsb_maneuver'))}</td><td>{len(tagged(black_games, 'lsb_maneuver'))*100//max(1,n_black)}%</td></tr>
<tr><td>g5 kingside push</td><td>{len(tagged(black_games, 'g5_push'))}</td><td>{len(tagged(black_games, 'g5_push'))*100//max(1,n_black)}%</td></tr>
<tr><td>e5 central break</td><td>{len(tagged(black_games, 'e5_break'))}</td><td>{len(tagged(black_games, 'e5_break'))*100//max(1,n_black)}%</td></tr>
<tr><td>Bxh2+ sacrifice</td><td>{len(tagged(black_games, 'bxh2_attack'))}</td><td>{len(tagged(black_games, 'bxh2_attack'))*100//max(1,n_black)}%</td></tr>
<tr><td>...Nd7 prophylaxis</td><td>{len(tagged(black_games, 'nd7_prophylaxis'))}</td><td>{len(tagged(black_games, 'nd7_prophylaxis'))*100//max(1,n_black)}%</td></tr>
<tr><td>Full wall (d5+e6+f5+c6)</td><td>{len(tagged(black_games, 'full_wall'))}</td><td>{len(tagged(black_games, 'full_wall'))*100//max(1,n_black)}%</td></tr>
<tr><td>Quick wins (≤20 moves)</td><td>{len(tagged(black_games, 'quick_win'))}</td><td>{len(tagged(black_games, 'quick_win'))*100//max(1,n_black)}%</td></tr>
</table>

<h3>Opponent Counterplay (White)</h3>
<table class="stat-table">
<tr><th>Opponent Break</th><th>Games</th><th>Notes</th></tr>
<tr><td>...Nc6 (threatens e5)</td><td>{len(tagged(white_games, 'opp_nc6'))}</td><td>⚠️ Very common — see Section 10</td></tr>
<tr><td>...f5 (mirror/Dutch SW)</td><td>{len(tagged(white_games, 'vs_symmetrical'))}</td><td>🟡 Creates locked center — see Sections 5-7</td></tr>
<tr><td>...e5 (central counter)</td><td>{len(tagged(white_games, 'vs_e5'))}</td><td>⚠️ Frequent</td></tr>
<tr><td>...b6 (queenside fianchetto)</td><td>{len(tagged(white_games, 'opp_b6'))}</td><td>⚠️ Bb7 threat — see Section 10</td></tr>
<tr><td>...Qb6 (d4 pin)</td><td>{len(tagged(white_games, 'opp_qb6'))}</td><td>🔴 Dangerous! See Section 10</td></tr>
</table>

<!-- ============================================================ -->
<h2 class="themes-section">5. Ne5/Ne4 Before Castling — When to Delay Castling</h2>
<!-- ============================================================ -->

{diagram_html(
    'r1bq1rk1/pp3ppp/2nbpn2/2ppN3/3P1P2/2PBP3/PP1N2PP/R1BQK2R w KQ - 0 9',
    'Ne5 before castling. Black has played ...c5 and ...Bd6 — threatening ...cxd4 exd4 leaving f4 hanging to Bxf4. Aman jumps Ne5 immediately to seize the initiative before castling.',
    arrows=[chess.svg.Arrow(chess.C5, chess.D4, color='#0000ffcc'),
            chess.svg.Arrow(chess.D6, chess.F4, color='#0000ffaa')]
)}

<p>Conventional wisdom says castle early. But Aman delays castling to play the knight outpost first in <strong>{len(tagged(white_games, 'ne5_before_castle'))} White games (Ne5)</strong> and <strong>{len(tagged(black_games, 'ne4_before_castle'))} Black games (Ne4)</strong> — a combined 19 games with an <strong>18-1 record</strong>. Black is a perfect <strong>{len(tagged(black_games, 'ne4_before_castle'))}-0</strong>. This is not recklessness — each case has a concrete reason.</p>

<h3>5a. White: Ne5 Before Castling ({len(tagged(white_games, 'ne5_before_castle'))} games, {len(tagged(white_games, 'ne5_before_castle'))-1}-1)</h3>

<h4>Trigger 1: Punishing Opponent's Time-Wasting</h4>
<div class="overview-box">
<p>When the opponent wastes tempi with queenside pawn pushes (a5, b5, a6, etc.) instead of developing, the position calls for <strong>immediate aggression</strong>. Castling is a quiet move — Ne5 punishes the opponent's slowness by seizing the outpost while they're underdeveloped.</p>
<p>From annotations (vs Noah278): <em>"He does it to punish the opponent's slowness out of the opening, with all of the queenside pawn pushes."</em></p>
</div>

{theme_box("Ne5 Punishing Tempo Waste", "Opponent wastes time with queenside pawn pushes. Ne5 seizes the initiative before they can develop.", tagged(white_games, 'ne5_bc_punish_tempo'), True, 1)}

<h4>Trigger 2: Blocking Bishop's Attack on the f4 Pawn</h4>
<div class="overview-box">
<p>When the opponent's bishop (often via ...Bd6 or after ...c5) threatens the f4 pawn, castling would leave the pawn vulnerable to <strong>cxd4 followed by Bxf4</strong>. Ne5 blocks the bishop's diagonal, so that after cxd4, we can safely recapture with exd4.</p>
<p>From annotations (vs bfk3): <em>"The reason for the urgency is that we want to block the bishop attacking our f pawn, so that on cxd4 we can recapture exd4."</em></p>
<p>From annotations (vs eugeniogonzalezrd): <em>"We would be forced to recapture with our c pawn here if we had delayed the Ne5 jump."</em></p>
</div>

{theme_box("Ne5 Blocking Bishop on f4", "Opponent's bishop threatens f4 pawn. Ne5 blocks the diagonal before castling.", tagged(white_games, 'ne5_bc_block_bishop'), True, 1)}

<h4>Trigger 3: Targeting Opponent's Bishop on g6</h4>
<div class="overview-box">
<p>When the opponent develops their bishop to g6 (common after ...Bg4→g6 or ...Bf5→g6), Ne5 attacks it directly. Capturing the bishop before castling is more urgent than king safety — you're winning the bishop pair and/or forcing structural concessions.</p>
<p>From annotations (vs tonka65): <em>"Aman decided to immediately leap to e5 here in order to take the bishop, even before castling."</em></p>
</div>

{theme_box("Ne5 Targeting Bishop on g6", "Opponent's bishop sits on g6. Ne5 attacks it directly — capturing is more urgent than castling.", tagged(white_games, 'ne5_bc_target_bg6'), True, 1)}

<h4>Trigger 4: Preventing Opponent's ...f5</h4>
<div class="overview-box">
<p>When you suspect the opponent is planning ...f5 (creating a symmetrical Stonewall), Ne5 before castling blocks the f5 push and denies the opponent their desired structure. Once ...f5 is in, your Ne5 can be challenged; better to establish it first.</p>
<p>From annotations (vs Sqeckle): <em>"He delays castling here because he thinks the opponent is planning to push f5."</em></p>
</div>

{theme_box("Ne5 Preventing ...f5", "Opponent threatens ...f5 (symmetrical SW). Ne5 blocks it before they can establish the structure.", tagged(white_games, 'ne5_bc_prevent_f5'), True, 1)}

<h4>Trigger 5: Castling Disrupted by Opponent</h4>
<div class="overview-box">
<p>Sometimes the opponent disrupts our castling plans — most notably with ...Qb6, which creates an X-ray pin on the d-file after any pawn exchanges. If we castle into the pin, the opponent can win the e5 pawn. Ne5 first sidesteps the problem.</p>
<p>From annotations (vs eugeniogonzalezrd): <em>"This queen move DOES X-RAY a pin should our opponent take cxd4, should we castle. So this move disrupts our usual move order."</em></p>
</div>

{theme_box("Ne5 — Castling Disrupted", "Opponent's moves (e.g. Qb6 pin) make castling dangerous. Ne5 sidesteps the problem.", tagged(white_games, 'ne5_bc_disrupted'), True, 1)}

<div class="surprise">
<strong>🔍 3 of {len(tagged(white_games, 'ne5_before_castle'))} White games: Never castled at all.</strong> In those games, the attack was so overwhelming from the center that castling was never needed. The king stayed in the center while pieces flooded the kingside.
</div>

<h3>5b. Black: Ne4 Before Castling ({len(tagged(black_games, 'ne4_before_castle'))} games, {len(tagged(black_games, 'ne4_before_castle'))}-0)</h3>

<p>A perfect record. With Black, the urgency to play Ne4 before castling is even higher — and the pattern is different from White.</p>

<h4>Primary Trigger: Blocking Rook Checks in the French Exchange</h4>
<div class="overview-box">
<p>In the French exchange variation (1.e4 e6 2.d4 d5 3.exd5 exd5), the e-file opens early. Black's king is exposed to <strong>Re1+ checks</strong>. Rather than waste time running the king to safety, <strong>Ne4 blocks the e-file</strong> while simultaneously occupying the dream square. Two problems solved with one move.</p>
<p>From annotations (vs Shipa1389): <em>"With black we often have the move Ne4 to block the rook's check on our king."</em></p>
<p>From annotations (vs grebenek): <em>"The knight blocking check is an idea when playing Stonewall as black. Perhaps the move order of Nf6, Bd6 actually encourages this rook check which we are actually happy to see."</em></p>
</div>

<div class="heuristic">
<strong>💡 Key Insight:</strong> In the French exchange Stonewall, don't fear Re1+. Play Nf6 before Bd6 — this <em>invites</em> Re1+ because you want to answer with Ne4, which blocks the check and establishes the outpost simultaneously. The "threat" actually helps Black.
</div>

{theme_box("Ne4 Blocking Rook Check (French Exchange)", "Open e-file gives White Re1+ check. Ne4 blocks the check AND establishes the outpost.", tagged(black_games, 'ne4_bc_block_check'), False, 1)}

<h4>Secondary Trigger: Forcing the Issue (Tempo Urgency)</h4>
<div class="overview-box">
<p>Black is a tempo down compared to White. This means there's less time for quiet development moves like castling. In several games, Aman plays Ne4 before castling simply because the position demands <strong>immediate action</strong> — forcing the opponent to deal with the knight before they can consolidate.</p>
<p>From annotations (vs VBKnight007): <em>"Knight before castling. Doing it early because we want to force the issue with the knight."</em></p>
<p>From annotations (vs noname2071980 / vs RafaelDm3): <em>"Perhaps black being a tempo down forces more directness / aggression."</em></p>
</div>

{theme_box("Ne4 Forcing the Issue (Tempo Urgency)", "Black is a tempo down — no time for quiet castling. Ne4 forces immediate resolution.", tagged(black_games, 'ne4_bc_force_issue'), False, 1)}

<h4>Tertiary Trigger: Exploiting a Weak e4 Square</h4>
<div class="overview-box">
<p>When the opponent's setup leaves e4 structurally weak (no pawn covering it, or opponent committed to a structure that can't challenge the knight), Aman jumps in immediately — before the opponent can shore up the weakness.</p>
<p>From annotations (vs DavidLaguna88): <em>"Avoiding the symmetrical stonewall. Aiming right for that weak e4 square."</em> And later: <em>"This knight on e4 was the dominating factor in black's win."</em></p>
</div>

{theme_box("Ne4 Exploiting Weak e4", "Opponent's structure leaves e4 undefended. Jump in before they can shore it up.", tagged(black_games, 'ne4_bc_exploit_weak'), False, 1)}

<div class="mirror-box">
<strong>🪞 White vs Black — Why Delay Castling?</strong><br>
<table class="stat-table">
<tr><th>Aspect</th><th>White (Ne5 before O-O)</th><th>Black (Ne4 before O-O)</th></tr>
<tr><td><strong>Record</strong></td><td>{len(tagged(white_games, 'ne5_before_castle'))-1}-1</td><td>{len(tagged(black_games, 'ne4_before_castle'))}-0 (perfect)</td></tr>
<tr><td><strong>Primary trigger</strong></td><td>Multiple (tempo, bishop, structure)</td><td>Blocking Re1+ check (French exchange)</td></tr>
<tr><td><strong>Philosophy</strong></td><td>Opportunistic — seize the moment</td><td>Structural — the outpost IS the defense</td></tr>
<tr><td><strong>Never castled</strong></td><td>3 games (attack from center)</td><td>2 games (endgame reached first)</td></tr>
</table>
</div>

<div class="heuristic">
<strong>💡 The Rule:</strong> Castle when it's safe and useful. But when Ne5/Ne4 solves a concrete problem (blocking, punishing, preventing), the outpost takes priority. The knight on e5/e4 often provides <em>more</em> king safety than castling would — it controls key squares and blocks enemy piece activity.
</div>

<!-- ============================================================ -->
<h2 class="themes-section">6. The e4 Central Break — Triggers, Plans & Timing</h2>
<!-- ============================================================ -->

{diagram_html(
    'rnbqkb1r/ppp2ppp/4pn2/3p4/3P1P2/3BP3/PPPN2PP/R1BQK1NR w KQkq - 0 5',
    'The e3 pawn: our structural weakness in the Stonewall — but also a loaded spring. When conditions are right, e4 transforms the position by opening the center, freeing the DSB, and creating tactical threats.',
    arrows=[chess.svg.Arrow(chess.E3, chess.E4, color='#22aa22aa')]
)}

<p>The e4 central break appears in <strong>{len(tagged(white_games, 'e4_break'))} of {n_white} games ({len(tagged(white_games, 'e4_break'))*100//max(1,n_white)}%)</strong> — and carries a <strong>100% win rate</strong>. When Aman pushes e4, he wins. Every time. This is not coincidence: the break only works when the position is ready, and Aman reads the signs accurately.</p>

<div class="insight">
<strong>📊 Key Stats:</strong> {len(tagged(white_games, 'e4_break'))} games with e4 break, all won. Average move: ~12-14. Most common after opponent plays ...c4 (71% e4 rate vs 41% without). Ne5 on the board in {len(tagged(white_games, 'e4_ne5_on_board'))} games. Opponent not castled in {len(tagged(white_games, 'e4_opp_not_castled'))} games.
</div>

<h3>6a. Signs That e4 Is Possible</h3>

<div class="overview-box">
<p>Not every position allows e4. These are the conditions that signal the break is ready:</p>
</div>

<p><strong>1. Opponent pushed ...c4 ({len(tagged(white_games, 'e4_after_c4'))} games)</strong></p>
<p>When the opponent pushes their c-pawn to c4 (usually attacking our LSB, which retreats to c2), they lock the queenside and <em>release the tension on d4</em>. This is the single strongest signal: <strong>71% of games with ...c4 feature an e4 break</strong>, versus 41% without. From annotations (vs <a href="https://lichess.org/study/bvfOTAKi/N56IBjR7">Atchi23</a>): <em>"We often want to time e4 for after our opponent has played c4."</em> And (vs <a href="https://lichess.org/study/bvfOTAKi/lALlJrhO">Collegeoflaw</a>): <em>"We very often see the e4 push after our opponent has lost the tension on d4 by playing c4."</em></p>
<p>However, timing matters. Against <a href="https://lichess.org/study/bvfOTAKi/N56IBjR7">Atchi23</a>, Aman played e4 <em>before</em> ...c4 and acknowledged it was an inaccuracy — the engine flagged it because it allows ...cxd4. The lesson: wait for ...c4 if it's coming.</p>

{theme_box("e4 After Opponent's ...c4", "Opponent locks the queenside with ...c4, freeing our e-pawn. The strongest trigger for the break.", tagged(white_games, 'e4_after_c4'), True, 2)}

<p><strong>2. We own the e4 square</strong></p>
<p>The break requires controlling e4 so the pawn isn't immediately lost or blocked. Key pieces: Nd2 (defends e4 after the push and recaptures), LSB on d3 or c2 (supports e4 and benefits from the opened diagonal), and sometimes the queen on e1, c2, or f3 providing additional cover. From annotations (vs <a href="https://lichess.org/study/jjmB1AcS/z5QkX8XW">Kriisi</a>): <em>"There is an important difference in this position — the bishop covering the e4 square through the knight and pawn. Qc2 is necessary to add another defender."</em></p>

<p><strong>3. Opponent is playing passively / KID setup ({len(tagged(white_games, 'e4_vs_kid'))} games)</strong></p>
<p>When the opponent plays ...g6/...Bg7/...d6 without committing central pawns, e4 seizes space and the center. From annotations (vs <a href="https://lichess.org/study/bvfOTAKi/LE4LuYsP">skyshor1</a>): <em>"Seems our main idea vs KID defense-like setups is this e4 push."</em> The opponent's fianchetto doesn't contest the center, making e4 natural and powerful.</p>

{theme_box("e4 vs KID/Passive Setups", "Opponent fianchettoes without committing central pawns. e4 punishes the passivity.", tagged(white_games, 'e4_vs_kid'), True, 2)}

<p><strong>4. Opponent is not taking our Ne5 ({len(tagged(white_games, 'e4_ne5_on_board'))} games)</strong></p>
<p>When Ne5 sits unchallenged, the opponent is under positional pressure but may not be collapsing. The e4 push becomes Plan B — a way to break open the position while the knight still dominates. From annotations (vs <a href="https://lichess.org/study/jjmB1AcS/37amt6Zv">Urano8</a>): <em>"Often if our opponent doesn't capture our e5 knight this is a plan B. This is how we will free up our d2 knight and DSB. If we can push e4 it usually means we can combine other opening/attacking ideas with the Stonewall."</em></p>

{theme_box("e4 With Ne5 On The Board (Plan B)", "Ne5 unchallenged — e4 opens the position while the knight dominates.", tagged(white_games, 'e4_ne5_on_board'), True, 2)}

<p><strong>5. Opponent is not castled ({len(tagged(white_games, 'e4_opp_not_castled'))} games)</strong></p>
<p>Opening the center against an uncastled king is devastating. The e4 break creates open lines that immediately threaten the exposed king. This is the most common condition — present in {len(tagged(white_games, 'e4_opp_not_castled'))} of {len(tagged(white_games, 'e4_break'))} e4 break games.</p>

<p><strong>6. After the LSB is traded ({len(tagged(white_games, 'e4_lsb_traded'))} games)</strong></p>
<p>When the opponent trades our LSB (Bxd3), it removes a defender from our camp — but it also eliminates a reason to keep the e3-d5 structure static. With the LSB gone, e4 opens lines for the remaining pieces (especially rooks on the e-file and d-file). The data shows a modest correlation: LSB traded before e4 in {len(tagged(white_games, 'e4_lsb_traded'))} of {len(tagged(white_games, 'e4_break'))} e4 games (20%), compared to 14% LSB trade rate across all 105 games. The more interesting finding: when the LSB <em>is</em> traded, e4 comes <strong>earlier</strong> (average move 12.9 vs 15.8 without the trade). This makes positional sense — without the LSB on d3, e4 is needed to generate activity through other means.</p>

{theme_box("e4 After LSB Traded", "LSB exchanged — e4 compensates by opening lines for rooks and remaining pieces.", tagged(white_games, 'e4_lsb_traded'), True, 2)}

<h3>6b. Eight Plans Revolving Around e4</h3>

<p>The e4 push isn't one idea — it serves different strategic purposes depending on the position:</p>

<p><strong>Plan 1: Blast open the center ({len(tagged(white_games, 'e4_blast_center'))} games)</strong></p>
<p>When our pieces are coordinated and the opponent's are not, e4 rips the position open to exploit superior development. The classic case is vs <a href="https://lichess.org/study/jjmB1AcS/AxGB7RbE">Inskaper0</a>: after ...f6 weakened e6, Aman saw e4 as a way to target the weakened structure. From annotations: <em>"Looking to blast open the position given our superior piece coordination. We are ready to attack. Our opponent is not ready to defend. As soon as Aman saw f6 he was thinking about trying to get e4 in."</em></p>

<p><strong>Plan 2: Free the DSB diagonal ({len(tagged(white_games, 'e4_free_bishop'))} games)</strong></p>
<p>The e3 pawn blocks the DSB's c1-h6 diagonal. Pushing e4 (and especially after ...dxe4 Nxe4) clears the way for the dark-squared bishop to become active. From annotations (vs <a href="https://lichess.org/study/jjmB1AcS/zEFBOQhQ">discopawn</a>): <em>"e4, while a great move to free up our minor pieces, would be bad [at that moment] as it would allow Nxe5."</em> — showing Aman evaluates the break even when he can't play it yet. Also (vs <a href="https://lichess.org/study/jjmB1AcS/X3EjQXZl">MunibertMomsen</a>): <em>"Our e4 break. Opening up the DSB."</em></p>

<p><strong>Plan 3: Plan B when Ne5 is ignored ({len(tagged(white_games, 'e4_plan_b'))} annotated games)</strong></p>
<p>If the opponent refuses to trade our Ne5 knight, we have a secondary plan. The e4 push frees the Nd2 and DSB while the knight continues to dominate e5. This combination — Ne5 + open center — is often overwhelming. Vs <a href="https://lichess.org/study/jjmB1AcS/37amt6Zv">Urano8</a> is the textbook example.</p>

<p><strong>Plan 4: Eliminate our weakness</strong></p>
<p>The e3 pawn is the structural weakness in our Stonewall. Pushing it to e4 (and exchanging it for d5) removes this liability. From annotations (vs <a href="https://lichess.org/study/jjmB1AcS/n2yNVTgE">AlexTurnbull</a>): <em>"If we can play e4, we usually want to. Getting rid of our weakness. Opening up the diagonal for our DSB."</em></p>

<p><strong>Plan 5: Take space against passive opponents ({len(tagged(white_games, 'e4_take_space'))} games)</strong></p>
<p>Against passive setups (especially KID-like structures), e4 grabs central space and pushes the opponent back. Vs <a href="https://lichess.org/study/jjmB1AcS/MqoD5v4N">livellozero</a> is the extreme case: Aman played e4 on move 8 against a passive ...d6/...b6/...Bb7 setup and it led to checkmate by move 11.</p>

<p><strong>Plan 6: Discover an attack ({len(tagged(white_games, 'e4_discovered_attack'))} games)</strong></p>
<p>The e4 push can uncover attacks from the d3 bishop or other pieces. Vs <a href="https://lichess.org/study/jjmB1AcS/SGWbiNQo">obrownu</a>: <em>"e4 — discovering an attack on the queen."</em> The pawn moves and suddenly a bishop or rook that was behind it gains a target.</p>

<p><strong>Plan 7: Create room for piece maneuvers</strong></p>
<p>After e4, the e3 square becomes available and the position opens up for rook lifts (Re1-e3), knight repositioning, and other piece activity. Vs <a href="https://lichess.org/study/jjmB1AcS/6thtrWst">On7even</a>: after Bxd3 Qxd3, the queen on d3 prepared e4 — and after exd5 Nxd5 Ne4, the knights found dominant squares in the opened center.</p>

<p><strong>Plan 8: Threaten a pawn fork ({len(tagged(white_games, 'e4_pawn_fork'))} games)</strong></p>
<p>When a knight sits on e5 and the opponent has pawns on c6 and e6, the e4 push threatens ...dxe4 followed by e5 forking knight and bishop, or Nxc6 followed by e5. Vs <a href="https://lichess.org/study/bvfOTAKi/awFCeisR">eugeniogonzalezrd</a>: <em>"e4 — threatening Nxc6 followed by e5 and a fork."</em></p>

<div class="heuristic">
<strong>💡 The Decision:</strong> These plans often overlap. A single e4 push might simultaneously free the bishop (Plan 2), eliminate the weakness (Plan 4), and discover an attack (Plan 6). The question isn't "which plan am I executing" but "are enough conditions met to make e4 worth the structural commitment?"
</div>

<h3>6c. Timing: When NOT to Play e4</h3>

<p>The <a href="https://lichess.org/study/bvfOTAKi/N56IBjR7">Atchi23</a> game provides the key cautionary tale: Aman played e4 and admitted it was an inaccuracy because the opponent still had ...cxd4 available. The e4 push changes the pawn structure irreversibly — if the opponent can exploit open lines or counter in the center, it backfires.</p>

<div class="overview-box">
<p><strong>Wait for e4 when:</strong></p>
<ul>
<li>The opponent's c-pawn can still capture on d4 (wait for ...c4 first)</li>
<li>Your pieces aren't coordinated enough to exploit the open lines</li>
</ul>
<p><strong>Push e4 when:</strong></p>
<ul>
<li>Opponent has committed with ...c4 (71% e4 rate — this is the green light)</li>
<li>You have Nd2 + LSB controlling the e4 square post-push</li>
<li>Opponent's king is still in the center</li>
<li>Ne5 is established and opponent refuses to trade it</li>
<li>Opponent is passive (KID/fianchetto) and you need central space</li>
</ul>
</div>

<!-- ============================================================ -->
<h2 class="themes-section">7. The g4 Kingside Storm — When, Why & How</h2>
<!-- ============================================================ -->

{diagram_html(
    'r1bq1rk1/ppp2ppp/2n1pn2/4N3/3P1PP1/3B1Q2/PPP4P/RNB2RK1 w - - 0 12',
    'The g4 kingside storm: Qf3 supports the push, Ne5 controls the center, g4 is about to rip open the g-file. After ...fxg4, Qxg4 or Bxg4 opens devastating lines.',
    arrows=[chess.svg.Arrow(chess.G4, chess.G5, color='#ff0000aa')]
)}

<p>The g4 push appears in <strong>{len(tagged(white_games, 'g4_storm'))} of {n_white} games ({len(tagged(white_games, 'g4_storm'))*100//max(1,n_white)}%)</strong> — nearly as common as e4, and the most dynamic attacking plan in the Stonewall. But it's not one plan — it has several distinct triggers.</p>

<h3>7a. g4 vs the ...e6 Structure</h3>
<div class="overview-box">
<p>When the opponent locks in their LSB with ...e6, they're structurally committed. <strong>Qf3 followed by a quick g4</strong> becomes the default aggressive plan. The logic: the opponent's light squares are permanently weakened, and the g4 push cracks them open further.</p>
<p><span class="key-stat">Appears in {len(tagged(white_games, 'g4_vs_e6'))} games</span> — the most common g4 trigger.</p>
</div>

{theme_box("g4 vs e6 — Key Games", "Opponent plays ...e6 early, locking in the LSB. White responds with Qf3 → g4.", tagged(white_games, 'g4_vs_e6'), True)}

<h3>7b. g4 vs the Symmetrical Stonewall</h3>
<div class="overview-box">
<p>When the opponent plays ...f5 (Dutch or symmetrical SW), the position locks up. The g4 push <strong>undermines the Black structure</strong>, especially loosening a knight on e4 (which is protected by the f5 pawn). Preparation: <strong>Kh1 + Rg1</strong> to support the pawn before pushing.</p>
<p><span class="key-stat">{len(tagged(white_games, 'g4_vs_symmetrical'))} games</span> <span class="key-stat">Kh1/Rg1 prep in {len(tagged(white_games, 'g4_kh1_rg1'))} games</span></p>
</div>

<div class="heuristic">
<strong>💡 Aman's Dilemma (evang_ili game):</strong> "You have to pick your poison—g3 or else face the SW." In symmetrical positions, g3 prevents ...Ne4 but blocks the DSB maneuver. g4 undermines ...Ne4 but requires preparation. Know the trade-off before choosing.
</div>

{theme_box("g4 vs Symmetrical SW — Key Games", "Opponent plays ...f5 creating a symmetrical structure. g4 undermines the position.", tagged(white_games, 'g4_vs_symmetrical'), True)}

<h3>7c. g4 After Early ...Bxf3 Knight Trade</h3>
<div class="overview-box">
<p>When the opponent trades their LSB for our f3 knight early (<strong>...Bxf3, Qxf3</strong>), we no longer have Ne5 — but the opponent is also <strong>weak on the light squares</strong>. The queen on f3 is perfectly placed to support a g4 push. We've lost a knight but gained the light-square initiative.</p>
<p><span class="key-stat">{len(tagged(white_games, 'g4_after_bxf3'))} games with this specific pattern</span></p>
</div>

{theme_box("g4 After ...Bxf3 — Key Games", "Opponent trades LSB for knight. No Ne5 available, but g4 exploits weakened light squares.", tagged(white_games, 'g4_after_bxf3'), True)}

<div class="mirror-box">
<strong>🪞 Black Mirror: The ...g5 Push ({len(tagged(black_games, 'g5_push'))} games, {len(tagged(black_games, 'g5_push'))*100//max(1,n_black)}%)</strong><br>
The Black equivalent of g4 exists but is much rarer. Usually deployed after castling and establishing Ne4. The asymmetry: White has Bd3 aimed at h7 providing natural support for kingside aggression; Black's Bd6 aims at h2 but doesn't synergize with ...g5 in the same way.
</div>

<!-- ============================================================ -->
<h2 class="themes-section">8. The Bad Bishop Maneuver — DSB (White) & LSB (Black)</h2>
<!-- ============================================================ -->

<p>Both sides have a "bad" bishop trapped behind their pawn chain. Activating it costs 3 tempi — so you need a good reason to invest that time.</p>

{diagram_html(
    'r1bq1rk1/ppp2ppp/2n1pn2/4N3/3P1P2/3B4/PPPB2PP/RN1Q1RK1 w - - 0 10',
    'The DSB maneuver path: Bc1→Bd2→Be1→Bh4. Three tempi to activate the "bad" bishop. Worth it when Ne5 plans are blocked (symmetrical SW or KID setups).',
    arrows=[
        chess.svg.Arrow(chess.D2, chess.E1, color='#00aa00cc'),
        chess.svg.Arrow(chess.E1, chess.H4, color='#00aa00cc'),
    ]
)}

<h3>8a. White: DSB Maneuver (Bd2→Be1→Bh4)</h3>
<p><span class="key-stat">{len(tagged(white_games, 'dsb_maneuver'))} games ({len(tagged(white_games, 'dsb_maneuver'))*100//max(1,n_white)}%)</span> <span class="key-stat">Full sequence to Bh4: {len(tagged(white_games, 'dsb_maneuver_full'))} games</span> <span class="key-stat">DSB never moves: {(n_white-len(tagged(white_games, 'dsb_maneuver')))*100//max(1,n_white)}%</span></p>

<h4>Trigger 1: Symmetrical Stonewall / Dutch</h4>
<div class="overview-box">
<p>When the opponent plays ...f5 (Dutch or symmetrical SW), recognize immediately: <strong>Nd2 is futile</strong> because ...Ne4 will be firmly rooted, protected by d5 and f5 pawns. Instead, switch to the DSB maneuver <em>before</em> playing Nd2 — otherwise Nd2 blocks the DSB's path and makes the maneuver impossible.</p>
<p>Aman's thinking (vs eetu2): "Elects for the DSB maneuver over keeping the knight out of e4."</p>
<p><span class="key-stat">{len(tagged(white_games, 'dsb_vs_symmetrical'))} games</span></p>
</div>

{theme_box("DSB Maneuver vs Symmetrical SW / Dutch", "Opponent plays ...f5. Nd2 is futile; switch to DSB maneuver before blocking it in.", tagged(white_games, 'dsb_vs_symmetrical'), True)}

<h4>Trigger 2: KID / Indian Setups (Uncommitted Center)</h4>
<div class="overview-box">
<p>When the opponent doesn't commit central pawns to the 4th/5th rank (no ...d5 or ...e5), they often fianchetto and control e5 from behind with pieces and flexible pawns. This makes it harder for our knight to reach e5, but also means the opponent can't support ...Ne4 with pawns. This gives us <strong>time to maneuver the DSB</strong> — get it to at least Be1 before committing Nd2.</p>
<p>Key recognition: the opponent's central pawns stay on d6/e6 (or d7/e7), not d5/e5. They control the center from behind rather than occupying it.</p>
<p><span class="key-stat">{len(tagged(white_games, 'dsb_vs_kid'))} games</span></p>
</div>

{theme_box("DSB Maneuver vs KID / Indian Setups", "Opponent has uncommitted center (no ...d5). Controls e5 from behind. Time to activate DSB.", tagged(white_games, 'dsb_vs_kid'), True)}

<div class="surprise">
<strong>🔍 When NOT to bother:</strong> In {(n_white-len(tagged(white_games, 'dsb_maneuver')))*100//max(1,n_white)}% of games, the DSB never moves at all. Don't waste time activating a bad piece when your good pieces (Bd3, Ne5) are already doing the job. The maneuver is for when the normal plans are denied.
</div>

<h3>8b. Black: LSB Maneuver (Bd7→Be8→Bh5)</h3>
<p><span class="key-stat">{len(tagged(black_games, 'lsb_maneuver'))} games</span> <span class="key-stat">Full to Bh5: {len(tagged(black_games, 'lsb_maneuver_full'))} games</span></p>

<h4>Trigger 1: Symmetrical Stonewall (opponent plays f4)</h4>
<div class="overview-box">
<p>The primary trigger. When the opponent plays f4, creating a symmetrical pawn structure, the LSB maneuver creates a favorable imbalance. Of the games where Aman starts the LSB maneuver early, <strong>the majority are against symmetrical structures</strong>.</p>
<p><span class="key-stat">{len(tagged(black_games, 'lsb_vs_symmetrical'))} games</span></p>
</div>

{theme_box("LSB Maneuver vs Symmetrical SW", "Opponent plays f4. Pawn structures mirror each other; LSB maneuver creates the imbalance.", tagged(black_games, 'lsb_vs_symmetrical'), False)}

<h4>Trigger 2: KIA / Indian Setups (Uncommitted Center)</h4>
<div class="overview-box">
<p>The <strong>exact mirror of White's DSB maneuver vs KID</strong>. When the opponent has an uncommitted center — g3 setup, no d4+e4 — they control e4 from behind, making it structurally harder for our Ne4 to be effective. So we switch to the LSB maneuver instead.</p>
<p>Aman's annotation: "Opponent is thwarting our Ne4 idea so time to play our LSB maneuver."</p>
<p>Key recognition: the opponent's central pawns aren't fully committed to the 4th rank, so our e4 outpost lacks the structural support it needs.</p>
<p><span class="key-stat">{len(tagged(black_games, 'lsb_vs_kia'))} games</span></p>
</div>

{theme_box("LSB Maneuver vs KIA / Indian Setups", "Opponent has uncommitted center (g3 without d4+e4). Ne4 denied structurally. Switch to LSB.", tagged(black_games, 'lsb_vs_kia'), False)}

<div class="mirror-box">
<strong>🪞 The Perfect Mirror:</strong><br>
<table class="stat-table">
<tr><th>Situation</th><th>White</th><th>Black</th></tr>
<tr><td>Symmetrical structure blocks normal plan</td><td>DSB maneuver vs ...f5</td><td>LSB maneuver vs f4</td></tr>
<tr><td>Indian-style setup blocks outpost</td><td>DSB maneuver vs KID (uncommitted center)</td><td>LSB maneuver vs KIA (uncommitted center)</td></tr>
<tr><td>Normal plan available (outpost open)</td><td>Leave DSB on c1 ({(n_white-len(tagged(white_games, 'dsb_maneuver')))*100//max(1,n_white)}%)</td><td>Play Ne4 instead ({len(tagged(black_games, 'ne4'))*100//max(1,n_black)}%)</td></tr>
</table>
</div>

<!-- ============================================================ -->
<h2 class="themes-section">9. Bishop Attacks on the Kingside</h2>
<!-- ============================================================ -->

<p>Two distinct bishop attack patterns appear in the Stonewall — one involving the LSB (Bd3) and one involving the DSB. Don't confuse them.</p>

{diagram_html(
    'r1bq1rk1/pppn1ppp/2nbp3/3p4/3P1P2/2PBPN2/PP1N2PP/R1BQ1RK1 w - - 0 10',
    "The Bxh7+ Greek Gift setup: Bd3 aimed at h7, Nf3 ready to jump Ng5+ after Kxh7. Key prerequisites: opponent's Nf6 has moved away (here Nd7), leaving h7 defended only by the king, and Bd6 does NOT cover g5 — so Ng5+ can't be captured.",
    arrows=[chess.svg.Arrow(chess.D3, chess.H7, color='#ff0000cc'),
            chess.svg.Arrow(chess.F3, chess.G5, color='#ff0000aa')]
)}

<h3>9a. Bxh7+ — The Greek Gift (True LSB Sacrifice)</h3>
<div class="overview-box">
<p>The Bd3 sacrifices itself on h7 with <strong>no piece supporting the capture</strong>. The return: exposed king, Ng5+ follows, queen reaches the h-file. Aman plays this with supreme confidence — the positional compensation is so overwhelming that precise calculation is secondary.</p>
<p><span class="key-stat">{len(tagged(white_games, 'bxh7_sac'))} true sacrifices</span> <span class="key-stat">{len(tagged(white_games, 'bxh7_supported'))} supported captures (rook/queen already on h-file)</span></p>
</div>

<div class="heuristic">
<strong>💡 Prerequisites:</strong> (1) Opponent castled kingside, (2) Knight on e5/f3 can jump to g5+ after ...Kxh7, (3) Queen can reach the h-file quickly, (4) Opponent's pieces can't defend the kingside.
</div>

{theme_box("Bxh7+ — True Sacrifices (no support)", "LSB sacrifice on h7 with no piece supporting. Ng5+ and Qh5 follow.", tagged(white_games, 'bxh7_sac'), True)}

{theme_box("Bxh7 — Supported Captures (rook/queen on h-file)", "Bxh7 with a rook or queen already aimed at the h-file. Still devastating, but not a pure sacrifice.", tagged(white_games, 'bxh7_supported'), True)}

<h3>9b. Bxh6 — The DSB Kingside Attack</h3>
<div class="overview-box">
<p>A different pattern entirely. When the opponent plays ...h6 (often to prevent Ng5 or Bg5), the DSB <strong>captures the h6 pawn</strong>, ripping open the kingside. The queen is typically already on the h-file ready to recapture. Not always a true sacrifice — sometimes the h6 pawn is pinned or the capture is otherwise safe — but always devastating for Black's king safety.</p>
<p><span class="key-stat">{len(tagged(white_games, 'bxh6_attack'))} games</span></p>
</div>

{theme_box("Bxh6 — DSB Kingside Attack", "DSB captures h6 pawn. Queen often ready to recapture. Rips open kingside shelter.", tagged(white_games, 'bxh6_attack'), True)}

<h3>9c. Rxf3 / Exchange Sac on f3</h3>
<div class="overview-box">
<p>A recurring attacking motif from the refreshed notes: once the <strong>queen reaches the h-file</strong> and <strong>both bishops</strong> are cutting toward the king, White can crash a rook into <strong>f3</strong> to drag the king out or strip key defenders. This is not a random exchange sac — it works when the h-file and bishop diagonals are already alive.</p>
<p><span class="key-stat">{len(tagged(white_games, 'rxf3_sac'))} games</span></p>
</div>

{theme_box("Rxf3 / Exchange Sac Motif", "Rook crashes into f3 once the h-file and bishop diagonals are primed.", tagged(white_games, 'rxf3_sac'), True)}

<!-- ============================================================ -->
<h2 class="threats-section">10. Opponent Threats & How to Handle Them</h2>
<!-- ============================================================ -->

<p>Recognizing opponent ideas early is as important as executing your own plans. Here are the most common threats and Aman's responses.</p>

<h3>10a. ...Bb7 — Threatens to Force Ne4</h3>
<div class="overview-box">
<p>The fianchettoed bishop x-rays the e4 square. Combined with ...Nf6, it threatens to establish an iron ...Ne4. <strong>Response: Qf3</strong> — adds a defender to e4 while also supporting g4 pawn push ideas. The queen on f3 does double duty: defensive anchor + attacking platform. The opponent's LSB is somewhat offside on b7.</p>
<p><span class="key-stat">{len(tagged(white_games, 'opp_bb7'))} games with ...Bb7</span></p>
</div>

{theme_box("vs ...Bb7 — Key Games", "Opponent fianchettoes LSB. Qf3 defends e4 and prepares g4.", tagged(white_games, 'opp_bb7'), True)}

<h3>10b. ...b6 — Threatens Bb7</h3>
<div class="overview-box">
<p>The pawn push prepares ...Bb7. If this happens before we've played f4, we're in trouble: the bishop targets our undefended e4 square and the diagonal is open. <strong>Response: Play f4 early</strong> if you see ...b6, so that you can answer ...Bb7 with Nf3, defending the pawn on the diagonal.</p>
<p><span class="key-stat">{len(tagged(white_games, 'opp_b6'))} games with ...b6</span></p>
</div>

<h3>10c. ...Nc6 — Threatens ...e5</h3>
<div class="overview-box">
<p>When played in the opening, ...Nc6 threatens ...e5, challenging our center directly. <strong>Response: f4</strong> stops ...e5 in many cases and solidifies the Stonewall structure. This is one reason f4 sometimes comes before Bd3.</p>
<p><span class="key-stat">{len(tagged(white_games, 'opp_nc6'))} games — the most common opponent development</span></p>
</div>

<h3>10d. ...Qb6 — Pins the d4 Pawn</h3>
<div class="overview-box">
<p>Looks like a mistaken anti-London play targeting the b-pawn (which is defended by our DSB since we're NOT playing the London). But the <strong>real danger</strong>: after cxd4/exd4, the d4 pawn is pinned to the king. This means the opponent can capture our e5 lance pawn with a knight and we <strong>cannot recapture with the pinned d-pawn</strong>.</p>
<p><strong>Response: Kh1</strong> — calmly breaking the pin, or ensuring you don't play into the pin.</p>
<p>From the annotations: "The threat is NOT b2. It is that the queen pins the d pawn which makes Nxe5 a threat."</p>
<p><span class="key-stat">{len(tagged(white_games, 'opp_qb6'))} games with ...Qb6</span></p>
</div>

{theme_box("vs ...Qb6 Pin — Key Games", "Opponent pins d4 pawn. Dangerous after cxd4/exd4. Kh1 or prophylaxis needed.", tagged(white_games, 'opp_qb6'), True)}

<h3>10e. ...Bd6 + ...c5 — f-Pawn Weakness</h3>
<div class="overview-box">
<p>The combination of ...Bd6 and ...c5 threatens our pawn structure. After cxd4/exd4, we often leave the f4 pawn undefended (because Nd2 blocks the DSB from defending it). <strong>Response: g3</strong> to support the f-pawn from below.</p>
<p>Trade-off: g3 blocks the DSB maneuver (Bd2→Be1→Bh4) permanently. Choose wisely.</p>
<p><span class="key-stat">{len(tagged(white_games, 'opp_bd6_c5'))} games</span></p>
</div>

{theme_box("vs ...Bd6 + ...c5 — Key Games", "Opponent combines Bd6 and c5 threatening f-pawn weakness after pawn exchanges.", tagged(white_games, 'opp_bd6_c5'), True)}

<h3>10f. a/b Pawn Pushes — Ba6 Forced Trade</h3>
<div class="overview-box">
<p>Opponent pushes queenside pawns to get their bad bishop to a6, where it can <strong>force a trade with our Bd3</strong>. This is dangerous because our Bd3 sits on the same diagonal as our Rf1 — the opponent can exploit the battery. <strong>Response: Re1</strong> (removing the rook from the diagonal) followed by <strong>Bc2</strong> to decline the trade.</p>
<p>From annotations (vs prikeee): "Allows us to avoid the Ba6 forcing of a bishop trade by calmly playing Bc2."</p>
<p>Interesting reversal: When Aman faces the SW as White (tony7209 game), he himself uses b3+Ba3 to trade off his bad bishop — showing this pattern works from both sides.</p>
<p><span class="key-stat">{len(tagged(white_games, 'opp_ba6_trade'))} games with explicit Ba6 threat</span></p>
</div>

{theme_box("vs Ba6 Forced Trade — Key Games", "Opponent pushes a/b pawns to get Ba6 and force a trade of our Bd3.", tagged(white_games, 'opp_ba6_trade'), True)}

<!-- ============================================================ -->
<h2 class="themes-section">11. Games by Theme — Quick Reference</h2>
<!-- ============================================================ -->

<h3>White — Attack Patterns</h3>
'''

# White themes - organized by new structure
for tag, title, desc in WHITE_ATTACK_THEMES:
    matching = tagged(white_games, tag)
    if matching:
        html += theme_box(title, desc, matching, True)

html += '<h3>White — Structural Themes</h3>'

for tag, title, desc in WHITE_STRUCTURAL_THEMES:
    matching = tagged(white_games, tag)
    if matching:
        html += theme_box(title, desc, matching, True)

html += '<h3>White — Opponent Threats</h3>'

for tag, title, desc in WHITE_THREAT_THEMES:
    matching = tagged(white_games, tag)
    if matching:
        html += theme_box(title, desc, matching, True)

html += '<h3>Black — Plans & Patterns</h3>'

for tag, title, desc in BLACK_THEMES:
    matching = tagged(black_games, tag)
    if matching:
        html += theme_box(title, desc, matching, False)

html += '<h3>Black — By Opening</h3>'

for tag, title, desc in BLACK_OPENING_THEMES:
    matching = tagged(black_games, tag)
    if matching:
        html += theme_box(title, desc, matching, False)

html += f'''

<div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 6px; text-align: center; font-size: 10px; color: #888;">
    <strong>Source:</strong> wonestall Stonewall Speedrun games on Lichess Studies<br>
    All game links open in Lichess for analysis with engine and annotations.<br>
    Generated from {n_white} White + {n_black} Black games &bull; {today}
</div>

</body>
</html>'''

# Write HTML for debugging
from pathlib import Path
output_path = Path(os.environ.get('OPENING_GUIDE_OUTPUT', str(DEFAULT_GUIDE_PDF)))
write_guide_outputs(html, HTML_DEBUG, output_path, f'  {n_white} white + {n_black} black games')
