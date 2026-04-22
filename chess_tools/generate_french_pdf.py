#!/usr/bin/env python3
"""Generate French Defense Cheat Sheet PDF from sterkurstrakur game collection.

Prerequisites: Run tag_french.py first to generate /tmp/french_data.json
Usage: python3 generate_french_pdf.py
"""

import json
import chess
import chess.svg
import weasyprint
from datetime import datetime
from diagram_helpers import diagram_html, DIAGRAM_CSS

with open('/tmp/french_data.json') as f:
    data = json.load(f)

games = data['games']
n_games = len(games)
today = datetime.now().strftime("%B %d, %Y")


def game_link(g):
    """Generate a clickable game link."""
    opp = g['white']  # opponent is always white
    url = g['url']
    ch = g.get('chapter', '')
    theme_hint = ''
    if ch:
        ch = ch.strip()
        if ch.startswith('(') and ')' in ch:
            theme_hint = ch[1:ch.index(')')]
            theme_hint = f' <span class="theme-hint">({theme_hint})</span>'
    result_icon = '✓' if g['result'] == '0-1' else ('½' if g['result'] == '1/2-1/2' else '✗')
    if url:
        return f'<a href="{url}">{opp}</a> {result_icon}{theme_hint}'
    return f'{opp} {result_icon}{theme_hint}'


def game_list_html(game_list, columns=2):
    """Generate a UL game list."""
    if not game_list:
        return '<p class="empty">No games found.</p>'
    rows = ''.join(f'<li>{game_link(g)}</li>' for g in game_list)
    col_class = f'columns: {columns};' if columns > 1 else ''
    return f'<ul class="game-list" style="{col_class}">{rows}</ul>'


def theme_box(title, description, game_list, columns=2):
    """Generate a themed game section."""
    if not game_list:
        return ''
    return f'''<div class="theme-group">
    <h4>{title} <span class="count">({len(game_list)} games)</span></h4>
    <p class="theme-desc">{description}</p>
    {game_list_html(game_list, columns)}
    </div>'''


def tagged(tag):
    """Filter games by tag."""
    return [g for g in games if tag in g.get('tags', [])]


def tagged_multi(*required_tags):
    """Filter games having ALL specified tags."""
    return [g for g in games if all(t in g.get('tags', []) for t in required_tags)]


def by_var(var_name):
    """Filter games by variation."""
    return [g for g in games if g.get('variation') == var_name]


# Counts
n_exchange = len(tagged('exchange_family'))
n_advanced = len(tagged('advanced_family'))
n_winawer = len(tagged('winawer'))
n_tarrasch = len(by_var('tarrasch'))
n_other = len(by_var('other'))
n_kia = len(by_var('kia'))
n_wins = len(tagged('win'))

# ============================================================
# Pre-compute diagrams (can't have backslashes in f-strings)
# ============================================================
DIAG_OVERVIEW = diagram_html(
    'rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3',
    'The French pawn structure after 1.e4 e6 2.d4 d5. Black challenges the center directly. Everything flows from this moment — White must choose a variation, and each one gives Black a different strategic plan.',
    flipped=True
)

DIAG_BAD_LSB = diagram_html(
    'r1bqk2r/ppp2ppp/2n1pn2/3p4/3PP3/2N2N2/PPP2PPP/R1BQKB1R b KQkq - 0 5',
    "The bad LSB problem: Black's c8 bishop is completely blocked by e6 and d5. It has no active diagonal. Every French variation offers a different solution to free or trade this piece.",
    flipped=True
)

DIAG_EXCHANGE = diagram_html(
    'rnbqkbnr/ppp2ppp/8/3p4/3P4/8/PPP2PPP/RNBQKBNR w KQkq - 0 3',
    'Exchange French after 3.exd5 exd5: symmetrical center, open e-file. The bad LSB problem is eased — now choose between Stonewall setup (Plan A), Aggressive O-O-O (Plan B), or Conservative O-O (Plan C).',
    flipped=True
)

DIAG_ADVANCED = diagram_html(
    'r1b1kb1r/pp3ppp/1qn1p3/2ppPn2/3P4/2P2N2/PP1NBPPP/R1BQ1RK1 b - - 0 10',
    "Advanced French: Black's ideal setup achieved — Qb6 + Nc6 + c5 = triple pressure on d4 (the chain's base). Nf5 on the outpost (protected by e6). Attack the base, not the tip.",
    arrows=[chess.svg.Arrow(chess.C5, chess.D4, color='#0000ffcc'),
            chess.svg.Arrow(chess.C6, chess.D4, color='#0000ffaa')],
    flipped=True
)

DIAG_WINAWER = diagram_html(
    'rnbqk2r/ppp2ppp/4pn2/3p4/1b1PP3/2N2N2/PPP2PPP/R1BQKB1R w KQkq - 0 4',
    'The Winawer: 3...Bb4 pins the Nc3. Aman plays this 100% of the time against Nc3. After e5, the battle for light squares begins — b6 then Ba6 trades the bad LSB.',
    arrows=[chess.svg.Arrow(chess.B4, chess.C3, color='#0000ffcc')],
    flipped=True
)

DIAG_CONSERVATIVE = diagram_html(
    'r1b1r1k1/ppqn1pp1/2pb1n1p/3p4/5P2/1BNP3P/PPP1N1P1/R1BQ1R1K w - - 3 12',
    "The ideal conservative setup: Re8 seizes the open e-file, Qc7 creates a battery with the Bd6 (eyeing h2), Nbd7 is flexible (supports Ne5/Nc5). From here Black grinds — the position is comfortable with no weaknesses.",
    arrows=[chess.svg.Arrow(chess.E8, chess.E1, color='#0000ffcc'),
            chess.svg.Arrow(chess.C7, chess.H2, color='#ff0000aa')],
    flipped=True
)

DIAG_NVB_ENDGAME = diagram_html(
    '8/pp3kpp/4p3/3p1p2/3PnP2/8/PP4PP/2B3K1 b - - 0 30',
    "Knight vs Bad Bishop endgame: Black's Ne4 dominates from the outpost, doubly supported by d5 and f5 — untouchable by White pawns. White's dark-squared bishop is trapped behind its own d4/f4 pawns with nothing to do. This is the endgame Black aims for in the French.",
    flipped=True
)

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

h2.french-section {{ background: #1a3a5c; }}
h2.exchange-section {{ background: #2d5016; }}
h2.advanced-section {{ background: #7a3b0e; }}
h2.winawer-section {{ background: #4a1a6b; }}
h2.lsb-section {{ background: #8b1a1a; }}
h2.endgame-section {{ background: #0d4f2b; }}
h2.disruption-section {{ background: #6b3a1a; }}
h2.themes-section {{ background: #2c3e50; }}

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
    border-left: 4px solid #1a3a5c;
    padding: 10px 14px;
    margin: 8px 0;
    border-radius: 0 4px 4px 0;
}}

.overview-box.exchange {{ border-left-color: #2d5016; }}
.overview-box.advanced {{ border-left-color: #7a3b0e; }}
.overview-box.winawer {{ border-left-color: #4a1a6b; }}
.overview-box.endgame {{ border-left-color: #0d4f2b; }}

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

.warning {{
    background: #fff3e0;
    border: 1px solid #ff9800;
    padding: 8px 12px;
    margin: 8px 0;
    border-radius: 4px;
}}

.warning strong {{ color: #e65100; }}

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

.decision-tree {{
    background: #f0f4f8;
    border: 1px solid #c8d6e5;
    padding: 10px 14px;
    margin: 8px 0;
    border-radius: 4px;
    font-size: 10px;
}}

.decision-tree strong {{ color: #1a3a5c; }}

{DIAGRAM_CSS}
</style>
</head>
<body>

<h1>The French Defense Playbook</h1>
<p class="subtitle">A Data-Driven Cheat Sheet from {n_games} Games<br>
Based on Aman Hambleton's (sterkurstrakur) French Defense Speedrun &bull; Generated {today}</p>

<div class="toc">
<strong>Contents</strong>
<ol>
<li>Overview — The French at a Glance</li>
<li>The Bad LSB — The Central Strategic Problem</li>
<li>The Exchange Variation — Three Plans</li>
<li>The Advanced Variation — Attacking the Chain</li>
<li>The Winawer — Positional Boldness</li>
<li>The Tarrasch & Sidelines</li>
<li>Opponent Disruptions — What Stops Our Plans</li>
<li>The Knight vs Bad Bishop Endgame</li>
<li>Statistics Deep Dive</li>
<li>Games by Theme</li>
</ol>
</div>

<!-- ============================================================ -->
<h2 class="french-section">1. Overview — The French at a Glance</h2>
<!-- ============================================================ -->

<div class="overview-box">
<p><strong>The French Defense: 1.e4 e6</strong> — We immediately signal that the center will be contested, not surrendered. The pawn on e6 supports ...d5 on the next move, challenging White's e4 directly.</p>
<p><strong>The deal:</strong> We get a solid, closed center and clear strategic plans. The price? Our light-squared bishop gets locked behind the e6/d5 pawn chain — the "bad French bishop." Almost every plan in the French revolves around either solving this problem or making it irrelevant.</p>
<p><strong>The speedrun record:</strong> <span class="key-stat">{n_wins}/{n_games} wins ({n_wins*100//n_games}%)</span> <span class="key-stat">1 draw</span> <span class="key-stat">1 loss (likely vs Stockfish)</span></p>
</div>

{DIAG_OVERVIEW}

<h3>Variation Breakdown</h3>
<table class="stat-table">
<tr><th>Variation</th><th>Games</th><th>Description</th></tr>
<tr><td><strong>Exchange</strong> (3.exd5 exd5)</td><td>{n_exchange}</td><td>Open center. Three sub-plans depending on opponent's play.</td></tr>
<tr><td><strong>Advanced</strong> (3.e5)</td><td>{n_advanced}</td><td>Closed center. Attack the d4 pawn chain from below.</td></tr>
<tr><td><strong>Winawer</strong> (3.Nc3 Bb4)</td><td>{n_winawer}</td><td>Pin the knight, trade the bad bishop. Positional sacrifice of DSB for light-square control.</td></tr>
<tr><td><strong>Tarrasch</strong> (3.Nd2)</td><td>{n_tarrasch}</td><td>Higher ELO variation. Treated similarly to Advanced with c5 break.</td></tr>
<tr><td><strong>Sidelines</strong> (2.Nf3, 2.f4, etc.)</td><td>{n_other + n_kia}</td><td>Irregular responses. Aman adapts flexibly.</td></tr>
</table>

<div class="heuristic">
<strong>💡 The Core Principle:</strong> The French is <em>reactive</em> — our plan depends heavily on which variation White chooses. But the strategic thread is constant: solve or exploit the bad LSB, fight for the center, and aim for favorable endgames where our knight outshines their bishop.
</div>

<!-- ============================================================ -->
<h2 class="lsb-section">2. The Bad LSB — The Central Strategic Problem</h2>
<!-- ============================================================ -->

<div class="overview-box">
<p>The light-squared bishop on c8 is trapped behind e6/d5. This is not just a French problem — it's <em>the</em> French problem. Every variation has a different solution, and choosing the right one is often the difference between a comfortable position and a cramped mess.</p>
</div>

{DIAG_BAD_LSB}

<h3>Solution 1: The Ba6 Trade (Winawer Advanced)</h3>
<div class="overview-box winawer">
<p>In the Winawer advanced, Aman plays <strong>b6 → Ba6</strong> to offer a direct trade of the bad LSB. We're willing to invest significant tempi — after the trade, we recapture with <strong>Nxa6</strong> (awkward!) and then reroute the knight via <strong>Nb8 → Nc6</strong> to a better square. The knight loses 3 tempi but the bishop was worth removing.</p>
<p><span class="key-stat">{len(tagged('lsb_ba6_trade'))} games with b6 + Ba6</span> <span class="key-stat">{len(tagged('nxa6_reroute'))} games with Nxa6 reroute</span></p>
</div>

{theme_box("Ba6 Trade — Key Games", "b6 followed by Ba6 to trade the bad LSB. Nxa6 then Nb8→Nc6 reroute.", tagged('lsb_ba6_trade'), 1)}

<h3>Solution 2: Development to g4/f5/e6 (Exchange Variation)</h3>
<div class="overview-box exchange">
<p>In the exchange variation, the e-file opens and the LSB is no longer structurally trapped. It develops naturally to the <strong>h7-b1 diagonal</strong> — typically <strong>Bg4</strong> (pinning the knight), <strong>Bf5</strong> (active post), or <strong>Be6</strong> (solid defense of d5). In many games, it gets traded on this diagonal, often via Bxd3 or Bxf1.</p>
<p><span class="key-stat">{len(tagged('lsb_bg4'))} games with Bg4</span> <span class="key-stat">{len(tagged('lsb_bf5'))} games with Bf5</span> <span class="key-stat">{len(tagged('lsb_be6'))} games with Be6</span> <span class="key-stat">{len(tagged('lsb_traded_diagonal'))} traded on the diagonal</span></p>
</div>

<h3>Solution 3: Bd7 → Bb5 (Advanced Variation)</h3>
<div class="overview-box advanced">
<p>In the advanced, the chain is closed. Aman sometimes uses <strong>Bd7 → Bb5</strong> to offer the trade on a different diagonal. Mentioned in annotations as an alternative to Qb6 — "starting with Qb6 to leave the option open to play Bd7, Bb5 to trade off the bad French bishop."</p>
<p><span class="key-stat">{len(tagged('lsb_bd7_bb5'))} games with Bd7-Bb5</span> <span class="key-stat">{len(tagged('lsb_bd7'))} games with Bd7</span></p>
</div>

<h3>Solution 4: Make It Irrelevant</h3>
<div class="overview-box">
<p>Sometimes you don't solve the bad bishop — you make it irrelevant. In many exchange games, Aman aims for <strong>knight vs bad bishop endgames</strong> where our knight dominates their remaining bishop. The French bishop isn't a problem if the game is won before it matters, or if the opponent's pieces are worse.</p>
<p><span class="key-stat">{len(tagged('knight_vs_bishop_endgame'))} games with N vs B endgame theme</span></p>
</div>

<div class="insight">
<strong>📊 Across all variations:</strong> The LSB was actively developed (Bg4/Bf5/Be6/Ba6/Bb5) in <strong>{len(tagged('lsb_developed')) + len(tagged('lsb_ba6_trade')) + len(tagged('lsb_bd7_bb5'))}</strong> of {n_games} games. In the rest, it either stayed home or the game ended before it mattered (quick wins, etc.). The message: actively solving the LSB problem is a priority, not an afterthought.
</div>

<!-- ============================================================ -->
<h2 class="exchange-section">3. The Exchange Variation — Three Plans</h2>
<!-- ============================================================ -->

<div class="overview-box exchange">
<p>After <strong>1.e4 e6 2.d4 d5 3.exd5 exd5</strong>, the center is symmetrical and open. The e-file is half-open. This is where the French gets interesting — we have <strong>three distinct plans</strong>, and the right choice depends on what our opponent does in the first few moves.</p>

{DIAG_EXCHANGE}
<p><span class="key-stat">{n_exchange} exchange games total</span> <span class="key-stat">{len(tagged('exchange_aggressive'))} aggressive</span> <span class="key-stat">{len(tagged('exchange_conservative'))} conservative</span> <span class="key-stat">{len(tagged('sw_reference'))} with SW discussion</span></p>
</div>

<h3>Plan A: The Stonewall Setup (f5, Nf6, O-O)</h3>
<div class="overview-box exchange">
<p>Push <strong>f5</strong> and go into a Stonewall-like structure with Nf6, Bd6, O-O. This is the dream — a familiar structure for wonestall enjoyers. But it's <strong>fragile</strong> and can be thwarted easily at higher ELOs.</p>
</div>

<div class="decision-tree">
<strong>🌳 When is the Stonewall safe?</strong><br><br>
<strong>✅ Green light (SW possible):</strong><br>
&nbsp;&nbsp;• Opponent plays <strong>Nf3</strong> (blocks Qh5+ check) AND wastes tempo (e.g. h3)<br>
&nbsp;&nbsp;• Opponent has no way to get Qh5+ or Qe2+ in<br>
&nbsp;&nbsp;• Opponent hasn't played c4 + Nc3 + O-O + Re1<br><br>
<strong>🔴 Red flags (SW dangerous):</strong><br>
&nbsp;&nbsp;• <strong>Qh5+</strong> or <strong>Qe2+</strong> early — disrupts our setup, may force us off-plan<br>
&nbsp;&nbsp;• <strong>c4 + Nc3</strong> — attacks our d5 pawn, may force us to drop a pawn<br>
&nbsp;&nbsp;• <strong>O-O + Re1+</strong> — rook check on the open e-file causes problems<br>
&nbsp;&nbsp;• <strong>Bc4 → Bb3</strong> — early bishop pressure on d5, very annoying<br><br>
<strong>Bottom line:</strong> The SW needs the opponent to cooperate. If they know what they're doing, it "will not scale past the level that our opponents start to really know what they're doing." At lower ELOs, "hope chess" works. At higher levels, look at Plans B or C.
</div>

<div class="warning">
<strong>⚠️ From the annotations:</strong> "Again, this is the way the SW can get us into a right mess." &bull; "Could get ourselves in trouble with the SW here." &bull; "Do we really want to try to force the SW and play these kinds of positions?" — Repeated warnings across {len(tagged('sw_reference'))} games.
</div>

{theme_box("Exchange with SW References", "Games where the Stonewall was discussed, attempted, or explicitly avoided.", tagged('sw_reference'), 1)}

<h3>Plan B: The Aggressive French Exchange (Bd6, Ne7, Bg4/Bf5/Be6, Qd7, O-O-O)</h3>
<div class="overview-box exchange">
<p>The punchy option. Develop the DSB to d6 (aimed at h2), knight to e7, LSB to g4/f5/e6, queen to d7, then <strong>castle queenside</strong> and launch the <strong>f6 + g5 + h5 pawn storm</strong>. This creates massive kingside attacking chances.</p>
<p><span class="key-stat">{len(tagged('exchange_aggressive'))} games with O-O-O</span> <span class="key-stat">{len(tagged('exchange_aggressive_full'))} with full setup (Bd6+Qd7+O-O-O)</span></p>
</div>

<div class="heuristic">
<strong>💡 Key detail — f6 and Bg5:</strong> In this setup, when the opponent plays <strong>Bg5</strong> pinning our knight to our king, we respond with <strong>f6</strong> — and we're happy about it. Why? Because (1) we wanted to play f6 anyway, (2) f6 controls g5 and e5, preventing knight infiltration, and (3) it prepares our g5 pawn push and kingside storm. The "pin" actually helps us. Appears in <strong>{len(tagged_multi('f6_control', 'opp_bg5_pin'))}</strong> games.
</div>

<div class="heuristic">
<strong>💡 Move order tip — Bd6 first:</strong> Aman mentions he likes to play Bd6 first when going aggressive. The reason: if the d-pawn is attacked (by Nc3), we want to respond with Ne7 — but Ne7 blocks the DSB if it hasn't been developed yet. DSB out first, then Ne7.
</div>

<div class="warning">
<strong>⚠️ What prevents Plan B?</strong><br>
• <strong>Nc3</strong> ({len(tagged('opp_nc3'))} games) — attacks d5 pawn immediately, may prevent smooth development<br>
• <strong>c4</strong> ({len(tagged('opp_c4'))} games) — strong disruption, forces us to respond to d5 pressure<br>
• <strong>Bc4 → Bb3</strong> ({len(tagged('opp_bc4_bb3'))} games) — bishop eyes d5, cramping<br>
• <strong>Qe2+</strong> ({len(tagged('opp_qe2_check'))} games) — may force early O-O instead of O-O-O; plan switches to Re8 pressure
</div>

{theme_box("Aggressive Exchange (O-O-O) — Key Games", "The attacking setup: Bd6, LSB development, Qd7, O-O-O, kingside storm.", tagged('exchange_aggressive'), 1)}

<h3>Plan C: The Conservative French Exchange (Bd6, c6, Nf6, O-O)</h3>
<div class="overview-box exchange">
{DIAG_CONSERVATIVE}
<p>The fallback. Develop solidly with <strong>Bd6, c6, Nf6, O-O</strong>. The most boring variation — little imbalance — but reliable and safe. Often followed by an <strong>h6 luft ("snork")</strong> and a Building Habits-style grind.</p>
<p>From the annotations: "It might be a boring set up but it allows us to get safely to the middle game with a comfortable position pretty much every time. Very habits-like, really."</p>
<p><span class="key-stat">{len(tagged('exchange_conservative'))} games with conservative setup</span> <span class="key-stat">{len(tagged('cons_re8_file'))} with Re8</span> <span class="key-stat">{len(tagged('cons_qc7_battery'))} with Qc7</span> <span class="key-stat">{len(tagged('cons_qs_expansion'))} with QS pawn expansion</span></p>
</div>

<h4>The Conservative Setup: Re8 + Qc7 + Nbd7</h4>
<div class="overview-box exchange">
<p>The conservative exchange is not just "boring and safe" — it has a concrete middlegame plan. After <strong>Bd6, c6, Nf6, O-O</strong>, the next phase is:</p>
<ol>
<li><strong>Re8</strong> — Seize the open e-file immediately after castling. The rook pressures e1 and any piece that lands on e5. In {len(tagged('cons_re8_file'))} of the O-O exchange games, Aman plays Re8 (typically moves 8-11).</li>
<li><strong>Qc7</strong> — Creates a battery with the Bd6, aiming down the c7-h2 diagonal toward White's king. Also keeps the bishop defended when the knight reroutes via Nbd7. Aman plays this in {len(tagged('cons_qc7_battery'))} games.</li>
<li><strong>Nbd7</strong> — Flexible knight placement ({len(tagged('cons_nbd7'))} games). Supports Nc5 (pressuring d3/e4), or Ne5 occupying the outpost. Also clears the way for Qc7 without blocking pieces.</li>
</ol>
<p><strong>Model sequence:</strong> ...Bd6, ...c6, ...Nf6, ...O-O, ...h6, ...Re8, ...Nbd7, ...Qc7 — then grind.</p>
<p><strong>Key example:</strong> vs nelson2127 — perfect setup: 8...Re8 9...Nbd7 10...Qc7, and after White's 11.Ng4?? the rook on e8 immediately punishes with Rxe1+.</p>
</div>

<h4>Queenside Pawn Expansion (b5-a5-b4)</h4>
<div class="overview-box exchange">
<p>In {len(tagged('cons_qs_expansion'))} exchange O-O games, Aman pushes queenside pawns as a secondary plan. This is not random — it's a positional idea that fits the symmetrical structure:</p>
<ul>
<li><strong>Space + piece activity:</strong> b5-a5 gains queenside space and opens lines for the rooks/bishop. The c8 bishop can develop to b7 behind the b-pawn.</li>
<li><strong>Create targets:</strong> ...b4 can hit a Nc3, destabilizing White's center control. If axb4, the a-file opens for Black's rook.</li>
<li><strong>Endgame squeeze:</strong> Connected passed pawns on the queenside become decisive in simplified positions.</li>
</ul>
<p><strong>Best example:</strong> vs miks121236 — 12...b5 13...a5 14...Nc5 15...b4 cracking open the queenside. White's 16.Bd2?? loses material to bxc3. The resulting pawn majority wins a 86-move grind.</p>
<p><strong>Even in losses:</strong> vs Laszar0v — 18...a5 and later 31...b5 as counterplay, though Black went wrong tactically. The idea was still correct.</p>
</div>

{theme_box("Conservative Exchange — Key Games", "Solid Bd6 + c6 + Nf6 + O-O setup. Safe fallback when aggressive plans are denied.", tagged('exchange_conservative'), 1)}

{theme_box("Re8 Open File Pressure", "Rook to the open e-file — the primary active idea in the conservative setup.", tagged('cons_re8_file'), 1)}

{theme_box("Queenside Pawn Expansion", "b5/a5 push — secondary plan creating queenside space and targets.", tagged('cons_qs_expansion'), 1)}

<div class="decision-tree">
<strong>🌳 Exchange Decision Tree:</strong><br><br>
1. Can you play the <strong>Stonewall</strong>? (Nf3 blocks checks, opponent wasted tempo, no c4+Nc3+Re1 threat)<br>
&nbsp;&nbsp;&nbsp;→ Yes → <strong>Plan A: f5, Nf6, O-O</strong> (SW structure)<br>
&nbsp;&nbsp;&nbsp;→ No → Continue to 2<br><br>
2. Can you play the <strong>Aggressive setup</strong>? (No immediate Nc3/c4/Bc4 pressure on d5, no Qe2+ forcing early O-O)<br>
&nbsp;&nbsp;&nbsp;→ Yes → <strong>Plan B: Bd6, Ne7, Bg4/Bf5/Be6, Qd7, O-O-O, pawn storm</strong><br>
&nbsp;&nbsp;&nbsp;→ No → Continue to 3<br><br>
3. Fall back to <strong>Conservative</strong>:<br>
&nbsp;&nbsp;&nbsp;→ <strong>Plan C: Bd6, c6, Nf6, O-O, then Re8 + Nbd7 + Qc7 → grind</strong><br>
&nbsp;&nbsp;&nbsp;→ Secondary plan: <strong>b5-a5 queenside expansion</strong> when center is stable
</div>

<h3>The Qe2+ Problem</h3>
<div class="overview-box exchange">
<p>When the opponent plays an early <strong>Qe2+</strong>, our plans shift. We often must castle kingside quickly (O-O) and pivot to <strong>Re8</strong> pressure on the open e-file to harass the exposed queen. The aggressive O-O-O plan is usually off the table, but the resulting positions still offer good chances.</p>
<p><span class="key-stat">{len(tagged('opp_qe2_check'))} games with Qe2+ disruption</span></p>
</div>

{theme_box("vs Qe2+ Disruption", "Early queen check forces a change of plans. Usually O-O followed by Re8 pressure.", tagged('opp_qe2_check'), 1)}

<!-- ============================================================ -->
<h2 class="advanced-section">4. The Advanced Variation — Attacking the Chain</h2>
<!-- ============================================================ -->

<div class="overview-box advanced">
{DIAG_ADVANCED}

<p>After <strong>1.e4 e6 2.d4 d5 3.e5</strong>, the center is locked. White has a space advantage but an overextended pawn chain. Our job: <strong>attack that chain from below</strong>. The primary targets are the d4 pawn (base) and the e5 pawn (tip).</p>
<p><span class="key-stat">{n_advanced} advanced games</span> <span class="key-stat">{len(tagged('qb6_pressure'))} with Qb6</span> <span class="key-stat">{len(tagged('d4_pressure'))} with Qb6+Nc6 combined</span></p>
</div>

<h3>The Core Plan: Qb6 + Nc6 + c5</h3>
<div class="overview-box advanced">
<p>Three pieces converge on d4:</p>
<ul>
<li><strong>Qb6</strong> — pressures d4 and threatens b2 (opponents frequently blunder the b2 pawn by moving their DSB out)</li>
<li><strong>Nc6</strong> — adds a third attacker on d4</li>
<li><strong>c5</strong> — the classic pawn lever against the chain base</li>
</ul>
<p>At lower ELOs, Aman starts with Qb6 first because opponents often blunder b2 immediately. At higher ELOs, Nc6 first to keep more flexibility.</p>
</div>

<div class="heuristic">
<strong>💡 Rule of thumb:</strong> If the opponent does not play c3, take with <strong>cxd4</strong>. Exchanging opens lines and removes the chain base. After cxd4, the DSB may be temporarily blocked, but the position opens up favorably.
</div>

<div class="insight">
<strong>📊 The b2 blunder:</strong> In <strong>{len(tagged('b2_grab'))}</strong> games, Aman won the b2 pawn after the opponent moved their DSB to defend d4. "Lower ELO players playing the French advanced find it very difficult to keep their pawn chain intact as they don't know the accurate way to defend and often collapse to queenside pressure."
</div>

<h3>The Ne7 → f5 Push</h3>
<div class="overview-box advanced">
<p>After the initial pressure with Qb6/Nc6/c5, the g8 knight comes to <strong>e7</strong> (not f6, which is blocked by e5). From e7, it supports a <strong>f5</strong> break — another attack on the pawn chain, this time from the other side. The cxd4 exchange may come first, temporarily blocking the DSB, but the position opens after f5.</p>
<p>Aman also uses <strong>Bd7</strong> in the advanced for flexible LSB deployment — potentially Bb5 to trade, or simply supporting the queenside.</p>
<p><span class="key-stat">{len(tagged_multi('ne7_develop', 'advanced_family'))} advanced games with Ne7</span> <span class="key-stat">{len(tagged('f5_break'))} games with f5 break</span></p>
</div>

<h3>An Important Note: The Closed Center</h3>
<div class="insight">
<strong>📊 No rush to castle:</strong> In the advanced French, the center is <em>closed</em>. Aman frequently delays or skips castling entirely. "One good aspect of the French is that the center is closed so there is often not a pressing need to castle." Many games are won with the king still in the center, using the extra tempi for the attack.
</div>

{theme_box("Qb6 + Nc6 Combined Pressure", "Both Qb6 and Nc6 target d4. The core advanced plan.", tagged('d4_pressure'), 1)}

{theme_box("b2 Pawn Grabs", "Opponents blunder the b2 pawn after moving their DSB. 'Pawn grabber Hambo strikes again!'", tagged('b2_grab'), 1)}

<!-- ============================================================ -->
<h2 class="winawer-section">5. The Winawer — Positional Boldness</h2>
<!-- ============================================================ -->

<div class="overview-box winawer">
{DIAG_WINAWER}

<p>After <strong>1.e4 e6 2.d4 d5 3.Nc3</strong>, we play <strong>3...Bb4</strong> — pinning the knight and preparing to trade or retreat. The Winawer is the sharpest mainline French and often leads to asymmetric pawn structures after White plays e5.</p>
<p><span class="key-stat">{n_winawer} Winawer games</span> <span class="key-stat">{len(by_var('winawer_advanced'))} advanced</span> <span class="key-stat">{len(by_var('winawer_exchange'))} exchange</span> <span class="key-stat">{len(by_var('winawer_ne2_gambit'))} Ne2 gambit</span></p>
</div>

<h3>Winawer Advanced: The b6 → Ba6 Plan</h3>
<div class="overview-box winawer">
<p>When White pushes e5 (Winawer advanced), Aman's plan is clear: <strong>b6 → Ba6</strong> — trading the bad LSB. After <strong>Nxa6</strong>, we accept the awkward knight and reroute it: <strong>Nb8 → Nc6</strong>. This costs tempi but eliminates the fundamental French weakness.</p>
<p>After the trade, we play positional chess. We'll be weak on dark squares (having traded the DSB for the pin earlier) but <strong>strong on light squares</strong>. Our central pawns create outposts for our knights. The endgame plan: reach <strong>Knight vs Bishop</strong> where our pawns are fixed on the right color.</p>
</div>

<div class="heuristic">
<strong>💡 The h6/h5 Idea:</strong> In the Winawer advanced, a common White plan is Nh3→Nf4 targeting e6 and d5. Aman's counter is <strong>h5</strong> — "doesn't make a lot of sense, but that's normally what the plan is." It prevents Nf4-g6 ideas and gains kingside space.
</div>

<div class="heuristic">
<strong>💡 Qg4 Counter:</strong> After Bb4, White can play <strong>Qg4</strong> attacking g7. This is a "nice counter to Bb4 for white." When White plays Nf3 first, Qg4 is prevented — which is good for us.
</div>

{theme_box("Winawer Advanced — Key Games", "The positional approach: b6, Ba6 trade, knight reroute, light-square control.", [g for g in games if g.get('variation') == 'winawer_advanced'], 1)}

<h3>Winawer Exchange: LSB Freed</h3>
<div class="overview-box winawer">
<p>When White exchanges (exd5 exd5) in the Winawer, the LSB is no longer bad — the e-file is open and the bishop has squares. "Because this transposed to the exchange our 'bad' French bishop is no longer bad." We can play Nc6 directly and bring the LSB to g4 or wherever it's needed.</p>
</div>

{theme_box("Winawer Exchange — Key Games", "Exchange in the Winawer frees the LSB. Flexible piece development.", [g for g in games if g.get('variation') == 'winawer_exchange'], 1)}

<h3>Winawer Ne2 Gambit: Why NOT Bxc3</h3>
<div class="overview-box winawer">
<p>When White plays <strong>4.Ne2</strong> instead of the mainline e5, the whole logic of the Winawer shifts. Normally, Bxc3+ is powerful because it <em>doubles White's pawns</em> — bxc3 creates a permanent structural weakness. But with Ne2 on the board, White recaptures <strong>Nxc3</strong> instead — no pawn damage at all.</p>
<p>From the annotations: <em>"We don't want to play Bxc3 because it just gets replaced by a knight."</em> And: <em>"The Ne2 makes our Bxc3 plan, b6, Ba6 plans etc., a lot less interesting so we go for regular development."</em></p>
</div>

<div class="heuristic">
<strong>💡 The Ba5 Retreat:</strong> Instead of trading on c3, Aman plays <strong>a3 Ba5</strong> — retreating the bishop to a useful diagonal. In both Ne2 games (TodorovicMilos, hallvardhf), the bishop goes to a5 after a3, never takes on c3. The bishop stays active, eyes the c3 square from a distance, and can reroute to b6 (pressuring d4) or stay on a5 depending on the position.
</div>

<div class="decision-tree">
<strong>🌳 Ne2 Gambit — Key Ideas:</strong><br><br>
<strong>DON'T:</strong> Play Bxc3 — Nxc3 recaptures cleanly, no structural damage to White<br>
<strong>DO:</strong> Retreat Ba5 after a3, develop Nc6, assault the center with f6 (if e5 is played)<br>
<strong>Castle:</strong> Prefer O-O. From the annotations: "we prefer O-O" — keep it simple<br>
<strong>Center play:</strong> "When the knight is not on f3 we need to assault the center"<br><br>
<strong>After e5 f6:</strong> The f-file opens. Nge7→Nf5 aims at d4. Qf7 eyes f2 after castling.<br>
<strong>After exd5:</strong> Transposes to exchange-like positions where Ne2 is slightly misplaced.
</div>

{theme_box("Winawer Ne2 Gambit — Key Games", "White plays 4.Ne2 instead of e5. Ba5 retreat, not Bxc3.", [g for g in games if g.get('variation') == 'winawer_ne2_gambit'], 1)}

<!-- ============================================================ -->
<h2 class="french-section">6. The Tarrasch & Sidelines</h2>
<!-- ============================================================ -->

<h3>The Tarrasch (3.Nd2)</h3>
<div class="overview-box">
<p>More common at higher ELOs. GM Naroditski recommended this against the French. Aman has two responses:</p>
<ul>
<li><strong>Main line: c5</strong> — treated similarly to the advanced. Take cxd4, recapture with the queen (which can't be harassed by knights since Nd2 blocks Nc3). Then develop with a6, b5, Bb7 ideas.</li>
<li><strong>Alternative: h6, a6 waiting moves</strong> — wait for White to commit before choosing a plan. Aman mentions this but it rarely appeared in the speedrun.</li>
</ul>
<p><span class="key-stat">{n_tarrasch} Tarrasch games</span> <span class="key-stat">{len(tagged('tarrasch_early_castle'))} with early O-O</span></p>
</div>

<div class="heuristic">
<strong>💡 Tarrasch tip:</strong> After cxd4, Qxd4 is playable because White's knight is on d2 (not c3), so there's no Nc3 tempo on the queen. "Again recapturing with the queen, which can't be harassed by white's knights."
</div>

<div class="insight">
<strong>📊 Castle Early, Castle Kingside:</strong> In the main c5 Tarrasch line, the plan is to castle kingside and <em>early</em>. The model sequence: <strong>c5 → cxd4/Qxd4 → Nf6 → Qd8 (or Qd7) → O-O</strong>. vs zulu666666 shows the ideal: O-O on move 8 with "nice easy development" and a comfortable position. When castling is delayed (SleezyMcCheesy, O-O on move 20), king safety becomes a recurring problem — "Aman thinks this may be an inaccuracy before castling." The Tarrasch gives an open position where the king needs shelter fast.
</div>

<div class="warning">
<strong>⚠️ Don't get cute:</strong> Games where Aman delayed castling in the Tarrasch got messy. vs dungeontrapz — never castled, had "queen developed off the back rank, a terrible LSB, and king in the middle of the board." vs More2Lose — never castled in the alternative h6/a6 line (though this was a high-level game where things moved too fast). The takeaway: in the standard c5 line, prioritize O-O over ambitious piece play.
</div>

{theme_box("Tarrasch — Key Games", "3.Nd2 variation. c5 main line, queen recaptures freely, castle early.", by_var('tarrasch'), 1)}

<h3>Sidelines (2.Nf3, 2.f4, 2.Nc3, 2.c4, KIA, etc.)</h3>
<div class="overview-box">
<p>Irregular White responses. The key insight: <strong>stick to the classical setup</strong>. Across {len([g for g in games if g.get('variation') in ('other', 'kia')])} sideline games, Aman plays c5 in {len(tagged('sideline_classical')) + len([g for g in tagged('c5_break') if g.get('variation') in ('other', 'kia')])} and Nc6 in {len([g for g in tagged('nc6_develop') if g.get('variation') in ('other', 'kia')])}. The message: when the opponent plays something strange, don't panic — play c5, Nc6, develop naturally, and castle when safe.</p>
<p><span class="key-stat">{len(tagged('sideline_classical'))} with classical c5 + Nc6</span></p>
</div>

<div class="heuristic">
<strong>💡 The Default Response to Weird Stuff:</strong> From the annotations — <em>"stick to what we know"</em> (vs GeneralAdorni, 2.Nf3) and <em>"Basically Aman plans to play this as a normal French advanced"</em> (vs santonegger, 2.f4). The classical setup (<strong>c5, Nc6, Bd7, O-O</strong>) works against almost everything because it's built on fundamental principles: contest the center, develop pieces, get the king safe. Don't try to "punish" weird openings — just play good chess.
</div>

<h4>King's Indian Attack (KIA)</h4>
<div class="overview-box">
<p>The KIA gets a specific response: <strong>Bd6, Ne7, Nc6, O-O</strong> (castled move 7 vs kkakdkk). Against g3 setups, if White closes the center with d5, this opens our LSB — and we aim for ...g5, ...f6 to shut down White's f4 break. <em>"If we can prevent f4 then our opponent's position is almost hopeless."</em></p>
</div>

<h4>2.f4 — The Nh6 Luxury</h4>
<div class="overview-box">
<p>When White plays f4 early, it gives us the <strong>Nh6→Nf5 route</strong> for free. Normally the knight must go via e7 (blocking the DSB temporarily), but f4 opens the h6 square. After c5, Nc6, Nh6→Nf5, we have excellent piece placement. <em>"Since our opponent played f4 it allows us the luxury of routing our knight via h6 to f5."</em></p>
</div>

{theme_box("Sidelines — Key Games", "Non-standard White responses. Classical setup: c5, Nc6, develop, castle.", [g for g in games if g.get('variation') in ('other', 'kia')], 1)}

<!-- ============================================================ -->
<h2 class="disruption-section">7. Opponent Disruptions — What Stops Our Plans</h2>
<!-- ============================================================ -->

<p>The French is reactive — our plans depend on what White does. Here are the most common disruptions and how Aman handles them.</p>

<h3>Nc3 — Attacks d5 ({len(tagged('opp_nc3'))} games, {len(tagged('opp_nc3'))*100//n_games}%)</h3>
<div class="overview-box">
<p>The most common disruption. The knight attacks our d5 pawn and often prevents our aggressive exchange setup. When Nc3 hits, we may need to defend d5 (with Be6, or c6) or pivot to the conservative plan.</p>
<p>From the annotations: "Again, we can't play our system here as the d5 pawn is hit."</p>
</div>

<h3>Qe2+ / Qh5+ — Queen Checks ({len(tagged('opp_queen_check'))} games)</h3>
<div class="overview-box">
<p>Early queen checks (especially Qe2+) force us to respond and often prevent the aggressive O-O-O setup. The typical response: <strong>castle kingside quickly (O-O) and pivot to Re8 pressure</strong> on the exposed queen. In some games, Qe2+ actually makes the Stonewall possible (because the queen blocks checks itself).</p>
</div>

<h3>c4 — Attacks the Center ({len(tagged('opp_c4'))} games)</h3>
<div class="overview-box">
<p>"That early c4 move by white is a killer when trying to force the SW." When White plays c4 before or alongside Nc3, our d5 pawn is under enormous pressure. Combined with O-O and Re1, White gets a very active position. This is why the Stonewall often fails at higher ELOs.</p>
</div>

<h3>Re1+ — Rook Check ({len(tagged('opp_re1_check'))} games)</h3>
<div class="overview-box">
<p>On the open e-file, White can play Re1+ which checks our king and forces us to deal with it — either blocking with a piece (losing that piece's flexibility) or moving the king (losing castling rights). Often comes as part of the c4 + Nc3 + O-O + Re1 battery that dismantles the Stonewall attempt.</p>
</div>

<h3>Bg5 — The Pin ({len(tagged('opp_bg5_pin'))} games, {len(tagged('opp_bg5_pin'))*100//n_games}%)</h3>
<div class="overview-box">
<p>A common move that pins our knight. In the aggressive exchange, we answer with <strong>f6</strong> — which we wanted to play anyway. f6 repels the bishop, controls e5 and g5, and prepares our pawn storm. The "pin" actually accelerates our plan. See Section 3 (Plan B) for details.</p>
</div>

<div class="stat-table">
<table class="stat-table">
<tr><th>Disruption</th><th>Games</th><th>Primary Response</th></tr>
<tr><td>Nc3</td><td>{len(tagged('opp_nc3'))}</td><td>Defend d5 (Be6/c6) or switch to conservative plan</td></tr>
<tr><td>Qe2+ / Qh5+</td><td>{len(tagged('opp_queen_check'))}</td><td>O-O quickly, Re8 pressure</td></tr>
<tr><td>c4</td><td>{len(tagged('opp_c4'))}</td><td>Take dxc4 or accept SW is off the table</td></tr>
<tr><td>Re1+</td><td>{len(tagged('opp_re1_check'))}</td><td>Block or accept tempo loss</td></tr>
<tr><td>Bg5</td><td>{len(tagged('opp_bg5_pin'))}</td><td>f6 — we wanted this anyway</td></tr>
<tr><td>Bc4/Bb3</td><td>{len(tagged('opp_bc4_bb3'))}</td><td>Defend d5, cramped but manageable</td></tr>
<tr><td>h3 (wasted tempo)</td><td>{len(tagged('opp_h3_tempo'))}</td><td>Exploit the tempo — SW may be possible!</td></tr>
</table>
</div>

<!-- ============================================================ -->
<h2 class="endgame-section">8. The Knight vs Bad Bishop Endgame</h2>
<!-- ============================================================ -->

<div class="overview-box endgame">
{DIAG_NVB_ENDGAME}

<p>A recurring theme across the speedrun: Aman steers toward <strong>knight vs bad bishop endgames</strong>. The idea is strategic — leave the opponent with a bishop that's restricted by its own pawns, while our knight can access every square.</p>
<p>This isn't unique to the French — it's a pattern across Aman's repertoire (Building Habits, Stonewall). But the French is particularly well-suited because the pawn structures naturally create outpost squares for the knight and lock in the opponent's remaining bishop.</p>
<p><span class="key-stat">{len(tagged('knight_vs_bishop_endgame'))} games with N vs B theme</span></p>
</div>

<h3>How to Get There</h3>
<div class="heuristic">
<strong>💡 Strategic principles:</strong><br>
• <strong>Trade one bishop, keep one knight</strong> — When facing the bishop pair, look to trade one of the opponent's bishops (preferably the active one). The remaining bishop becomes restricted.<br>
• <strong>Pawns on opposite color to our pieces</strong> — Place pawns on the <em>opposite</em> color of our remaining bishop (or on dark squares if we have a knight). This maximizes piece activity.<br>
• <strong>Look for c4, e4, f5 outposts</strong> — "c4 is an important square in the French. We see how it could become a strong outpost for our knight via Na5, Nc4. Especially strong in a N vs DSB endgame as our knight would be anchored on a light square."<br>
• <strong>Simplify when ahead</strong> — Trading into the endgame amplifies structural advantages. "We are happy to take [the trade]" is a frequent refrain.
</div>

<div class="insight">
<strong>📊 From the turtletaufiq game (a masterclass):</strong> "Positionally we are already better. We control g5 and e5 with our f pawn and prevent knight infiltration. We have the bishop pair." Aman then gradually simplifies, aiming for the N vs B endgame. "Look at the mobility of our bishop vs the opponent's. We can traverse the board at will. Our opponent is boxed in and restricted." Eventually: "c4 is an important square... knight anchored on a light square."
</div>

{theme_box("Knight vs Bad Bishop Endgame — Key Games", "Games where Aman steered toward a favorable N vs B endgame.", tagged('knight_vs_bishop_endgame'), 1)}

<!-- ============================================================ -->
<h2 class="themes-section">9. Statistics Deep Dive</h2>
<!-- ============================================================ -->

<h3>Variation Distribution</h3>
<table class="stat-table">
<tr><th>Variation</th><th>Games</th><th>%</th></tr>
<tr><td>Exchange (all)</td><td>{n_exchange}</td><td>{n_exchange*100//n_games}%</td></tr>
<tr><td>Advanced (non-Winawer)</td><td>{len(by_var('advanced'))}</td><td>{len(by_var('advanced'))*100//n_games}%</td></tr>
<tr><td>Winawer Advanced</td><td>{len(by_var('winawer_advanced'))}</td><td>{len(by_var('winawer_advanced'))*100//n_games}%</td></tr>
<tr><td>Winawer Exchange</td><td>{len(by_var('winawer_exchange'))}</td><td>{len(by_var('winawer_exchange'))*100//n_games}%</td></tr>
<tr><td>Winawer Ne2 Gambit</td><td>{len(by_var('winawer_ne2_gambit'))}</td><td>{len(by_var('winawer_ne2_gambit'))*100//n_games}%</td></tr>
<tr><td>Tarrasch</td><td>{n_tarrasch}</td><td>{n_tarrasch*100//n_games}%</td></tr>
<tr><td>Other/Sidelines</td><td>{n_other + n_kia}</td><td>{(n_other+n_kia)*100//n_games}%</td></tr>
</table>

<h3>Castling Patterns</h3>
<table class="stat-table">
<tr><th>Pattern</th><th>Games</th><th>%</th></tr>
<tr><td>O-O (kingside)</td><td>{len(tagged('castle_kingside'))}</td><td>{len(tagged('castle_kingside'))*100//n_games}%</td></tr>
<tr><td>O-O-O (queenside)</td><td>{len(tagged('castle_queenside'))}</td><td>{len(tagged('castle_queenside'))*100//n_games}%</td></tr>
<tr><td>Never castled</td><td>{n_games - len(tagged('castle_kingside')) - len(tagged('castle_queenside'))}</td><td>{(n_games - len(tagged('castle_kingside')) - len(tagged('castle_queenside')))*100//n_games}%</td></tr>
</table>

<h3>Key Move Frequencies</h3>
<table class="stat-table">
<tr><th>Our Move</th><th>Games</th><th>%</th><th>Context</th></tr>
<tr><td>Nc6</td><td>{len(tagged('nc6_develop'))}</td><td>{len(tagged('nc6_develop'))*100//n_games}%</td><td>Universal development move</td></tr>
<tr><td>c5 break</td><td>{len(tagged('c5_break'))}</td><td>{len(tagged('c5_break'))*100//n_games}%</td><td>Key pawn lever in advanced/Tarrasch</td></tr>
<tr><td>h6 snork</td><td>{len(tagged('h6_snork'))}</td><td>{len(tagged('h6_snork'))*100//n_games}%</td><td>Luft + prevents Bg5/Ng5</td></tr>
<tr><td>Ne7</td><td>{len(tagged('ne7_develop'))}</td><td>{len(tagged('ne7_develop'))*100//n_games}%</td><td>Key in both Winawer and exchange</td></tr>
<tr><td>Bb4 pin</td><td>{len(tagged('bb4_pin'))}</td><td>{len(tagged('bb4_pin'))*100//n_games}%</td><td>The Winawer move</td></tr>
<tr><td>h5 push</td><td>{len(tagged('h5_push'))}</td><td>{len(tagged('h5_push'))*100//n_games}%</td><td>Kingside expansion / prevents Nf4</td></tr>
<tr><td>Qb6</td><td>{len(tagged('qb6_pressure'))}</td><td>{len(tagged('qb6_pressure'))*100//n_games}%</td><td>Pressure on d4/b2 in advanced</td></tr>
<tr><td>f6</td><td>{len(tagged('f6_control'))}</td><td>{len(tagged('f6_control'))*100//n_games}%</td><td>Controls e5/g5, prepares storm</td></tr>
<tr><td>g5 push</td><td>{len(tagged('g5_push'))}</td><td>{len(tagged('g5_push'))*100//n_games}%</td><td>Kingside pawn storm</td></tr>
<tr><td>Bg4</td><td>{len(tagged('lsb_bg4'))}</td><td>{len(tagged('lsb_bg4'))*100//n_games}%</td><td>LSB development + pin</td></tr>
<tr><td>Bf5</td><td>{len(tagged('lsb_bf5'))}</td><td>{len(tagged('lsb_bf5'))*100//n_games}%</td><td>Active LSB on the diagonal</td></tr>
</table>

<h3>Game Length Distribution</h3>
<table class="stat-table">
<tr><th>Length</th><th>Games</th><th>%</th></tr>
<tr><td>Quick wins (≤20 moves)</td><td>{len(tagged('quick_win'))}</td><td>{len(tagged('quick_win'))*100//n_games}%</td></tr>
<tr><td>Medium (21-39 moves)</td><td>{n_games - len(tagged('quick_win')) - len(tagged('long_game'))}</td><td>{(n_games - len(tagged('quick_win')) - len(tagged('long_game')))*100//n_games}%</td></tr>
<tr><td>Long (40+ moves)</td><td>{len(tagged('long_game'))}</td><td>{len(tagged('long_game'))*100//n_games}%</td></tr>
</table>

<!-- ============================================================ -->
<h2 class="themes-section">10. Games by Theme</h2>
<!-- ============================================================ -->

<h3>By Variation</h3>
'''

# Variation themes
var_themes = [
    ('var_exchange', 'Exchange Variation', 'All exchange games (3.exd5 exd5).'),
    ('var_advanced', 'Advanced Variation', 'All advanced games (3.e5).'),
    ('var_winawer_advanced', 'Winawer Advanced', 'Winawer into advanced pawn structure.'),
    ('var_winawer_exchange', 'Winawer Exchange', 'Winawer into exchange pawn structure.'),
    ('var_winawer_ne2_gambit', 'Winawer Ne2 Gambit', 'Unusual 4.Ne2 in the Winawer.'),
    ('var_winawer_transposition', 'Winawer Transposition', 'Winawer arising from non-standard move orders.'),
    ('var_tarrasch', 'Tarrasch', '3.Nd2 variation.'),
    ('var_kia', 'KIA / King\'s Indian Attack', 'g3 setup from White.'),
    ('var_other', 'Other Sidelines', 'Non-standard White responses (2.Nf3, 2.f4, 2.Nc3, 2.c4, etc.).'),
]

for tag, title, desc in var_themes:
    matching = tagged(tag)
    if matching:
        html += theme_box(title, desc, matching)

html += '<h3>Exchange Sub-Plans</h3>'

exchange_themes = [
    ('exchange_aggressive', 'Aggressive Exchange (O-O-O)', 'The attacking setup: Bd6 + LSB + Qd7 + O-O-O + pawn storm.'),
    ('exchange_conservative', 'Conservative Exchange (O-O)', 'The solid setup: Bd6 + c6 + Nf6 + O-O. Safe fallback.'),
    ('cons_re8_file', 'Conservative: Re8 Open File', 'Re8 seizing the open e-file — the primary active idea.'),
    ('cons_qc7_battery', 'Conservative: Qc7 Battery', 'Qc7 creating a battery with Bd6 toward h2.'),
    ('cons_qs_expansion', 'Conservative: QS Pawn Expansion', 'b5/a5 push — queenside space and targets.'),
    ('sw_reference', 'Stonewall References', 'Games where the SW was discussed, attempted, or avoided.'),
    ('opp_qe2_check', 'vs Qe2+ Disruption', 'Early queen check forces plan change.'),
]

for tag, title, desc in exchange_themes:
    matching = tagged(tag)
    if matching:
        html += theme_box(title, desc, matching)

html += '<h3>Strategic Themes</h3>'

strategic_themes = [
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

for tag, title, desc in strategic_themes:
    matching = tagged(tag)
    if matching:
        html += theme_box(title, desc, matching)

html += '<h3>Opponent Disruptions</h3>'

disruption_themes = [
    ('opp_nc3', 'Opponent Nc3', 'Knight attacks d5 — the most common disruption.'),
    ('opp_bg5_pin', 'Opponent Bg5 Pin', 'Bishop pins our knight. Answered with f6.'),
    ('opp_queen_check', 'Opponent Queen Check (Qe2+/Qh5+)', 'Early queen check disrupts plans.'),
    ('opp_c4', 'Opponent c4', 'Attacks our d5 pawn — kills the SW.'),
    ('opp_re1_check', 'Opponent Re1+', 'Rook check on the open e-file.'),
    ('opp_h3_tempo', 'Opponent h3 (Tempo Waste)', 'Wasted tempo — may enable the Stonewall.'),
]

for tag, title, desc in disruption_themes:
    matching = tagged(tag)
    if matching:
        html += theme_box(title, desc, matching)

html += f'''

<div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 6px; text-align: center; font-size: 10px; color: #888;">
    <strong>Source:</strong> sterkurstrakur French Defense Speedrun games on Lichess Studies<br>
    All game links open in Lichess for analysis with engine and annotations.<br>
    Generated from {n_games} games &bull; {today}<br>
    ✓ = Black win &bull; ½ = Draw &bull; ✗ = Black loss
</div>

</body>
</html>'''

# Write HTML for debugging
with open('/tmp/french_cheatsheet.html', 'w') as f:
    f.write(html)

# Generate PDF
from pathlib import Path
output_path = Path(__file__).resolve().parent / 'french-cheatsheet.pdf'
weasyprint.HTML(string=html).write_pdf(str(output_path))
print(f'PDF generated: {output_path}')
print(f'  {n_games} games')
