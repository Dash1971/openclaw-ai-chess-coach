#!/usr/bin/env python3
"""Generate The Iron Laws of Opposite-Side Castling PDF with chess diagrams."""

import chess
import chess.svg
import weasyprint
import base64
from datetime import datetime

today = datetime.now().strftime("%B %d, %Y")


def board_svg(fen, size=280, arrows=None, squares=None, lastmove=None):
    """Generate SVG of a chess position."""
    board = chess.Board(fen)
    kwargs = {'size': size}
    if arrows:
        kwargs['arrows'] = arrows
    if squares:
        kwargs['fill'] = {sq: '#ff000044' for sq in squares}
    if lastmove:
        kwargs['lastmove'] = lastmove
    return chess.svg.board(board, **kwargs)


def svg_to_data_uri(svg_str):
    """Convert SVG string to data URI for embedding in HTML."""
    b64 = base64.b64encode(svg_str.encode()).decode()
    return f'data:image/svg+xml;base64,{b64}'


# ═══════════════════════════════════════════════════════════════════════════════
# POSITIONS — Illustrative FENs for each law
# ═══════════════════════════════════════════════════════════════════════════════

positions = {
    'race': {
        # Sicilian Dragon Yugoslav Attack — classic mutual pawn storm race
        'fen': 'r1b2rk1/pp2ppbp/2np1np1/q7/2BNP3/2N1BP2/PPPQ2PP/2KR3R w - - 0 12',
        'caption': 'Yugoslav Attack vs Dragon. White storms the kingside (h4-g4-h5), Black storms the queenside (a5-a4-b5). The race is on — every tempo counts.',
        'arrows': [
            chess.svg.Arrow(chess.H2, chess.H4, color='#ff0000cc'),
            chess.svg.Arrow(chess.G2, chess.G4, color='#ff0000cc'),
            chess.svg.Arrow(chess.A7, chess.A5, color='#0000ffcc'),
            chess.svg.Arrow(chess.B7, chess.B5, color='#0000ffcc'),
        ],
    },
    'pawns_storm': {
        # White about to launch g4-g5 storm
        'fen': 'r3kb1r/1bqn1ppp/p2ppn2/1p6/3NPP2/2N1B3/PPPQ2PP/2KR1B1R w kq - 0 12',
        'caption': 'White\'s plan: f4-f5 and g2-g4-g5 to rip open files near Black\'s king. The pawns go first — pieces follow through the gaps.',
        'arrows': [
            chess.svg.Arrow(chess.F4, chess.F5, color='#ff0000cc'),
            chess.svg.Arrow(chess.G2, chess.G4, color='#ff0000cc'),
        ],
    },
    'two_jobs': {
        # Position showing shield pawns vs attack pawns
        'fen': 'r4rk1/1b1nqppp/p2ppn2/1p6/3NPP2/2N1B1P1/PPPQ3P/1K1R1B1R w - - 0 14',
        'caption': 'White\'s a2-b2-c2 pawns = SHIELDS (don\'t push). Kingside f4-g3-h2 pawns = WEAPONS (push hard). Know the difference.',
        'arrows': [
            chess.svg.Arrow(chess.G3, chess.G4, color='#ff0000cc'),
            chess.svg.Arrow(chess.H2, chess.H4, color='#ff0000cc'),
        ],
    },
    'open_files': {
        # Rook bearing down an open file at the king
        'fen': 'r4rk1/1b1nq1pp/p2ppn2/1p3p2/3NPP2/2N1B3/PPPQ2PP/1K1R1B1R w - - 0 14',
        'caption': 'After g4 fxg4, the g-file rips open. White\'s rook on h1 swings to g1 — open file pointing at Black\'s king = lethal.',
        'arrows': [
            chess.svg.Arrow(chess.H1, chess.G1, color='#ff0000cc'),
            chess.svg.Arrow(chess.G1, chess.G7, color='#ff0000cc'),
        ],
    },
    'center': {
        # Closed center — storms work; if center opens, dynamics change
        'fen': 'r1b2rk1/pp1nqppp/4pn2/2ppP3/3P1P2/2PBB3/PP1NQ1PP/R3K2R w KQ - 0 12',
        'caption': 'French Advanced: closed center (d4-e5 chain). This is IDEAL for OSC — the locked pawns buy time for flank storms. But if Black plays ...f6 or ...cxd4 and opens it, the rules change instantly.',
        'arrows': [
            chess.svg.Arrow(chess.F7, chess.F6, color='#0000ffcc'),
        ],
    },
    'dont_trade': {
        # Active attacking piece vs passive defender
        'fen': '2kr3r/ppp1qppp/2n2n2/2b1p1B1/4P1b1/2NP1N2/PPP2PPP/R2QK2R w KQ - 0 9',
        'caption': 'White\'s Bg5 pins the f6 knight defending the king. DON\'T trade it for Black\'s passive pieces. Trade it only to remove a key defender (like Nf6 itself via Bxf6).',
        'arrows': [
            chess.svg.Arrow(chess.G5, chess.F6, color='#ff0000cc'),
        ],
    },
    'prophylaxis': {
        # Position where one defensive move prevents disaster
        'fen': 'r3k2r/1bqnbppp/p2ppn2/1p4B1/3NPP2/2N5/PPPQB1PP/2KR3R w kq - 0 12',
        'caption': 'Before launching g4, should White play Kb1 first? Yes — tucking the king into the corner costs one tempo but prevents back-rank tricks and ...Qa3+ ideas forever. One defensive tempo saves three later.',
        'arrows': [
            chess.svg.Arrow(chess.C1, chess.B1, color='#00aa00cc'),
        ],
    },
    'rooks_before_queen': {
        # Rooks on open files, queen held back
        'fen': '2kr4/ppp2ppp/2n1bn2/4p1q1/4P3/1BN2N2/PPP2PPP/2KRR3 w - - 0 14',
        'caption': 'White\'s rooks own the d and e-files. The queen stays back on d2 until the rooks create the breakthrough. Rooks first, queen finishes.',
        'arrows': [
            chess.svg.Arrow(chess.D1, chess.D7, color='#ff0000cc'),
        ],
    },
    'queen_trade': {
        # Emergency brake — losing the race, trade queens
        'fen': 'r3r1k1/1b3ppp/pqn1pn2/1p6/P2PP3/1BN2Q2/1PP3PP/2KR3R w - - 0 16',
        'caption': 'Black\'s attack (Qb6, a5-a4, Nc6-a5-b3) is faster than White\'s. Emergency option: Qf3-d3 offering the queen trade. No queens = no mating attack = their storm becomes just pawns.',
        'arrows': [
            chess.svg.Arrow(chess.F3, chess.B3, color='#00aa00cc'),
        ],
    },
    'french_osc': {
        # French Defense OSC position — Black castled QS, White KS
        'fen': '2kr1b1r/pppnqppp/4pn2/3pP3/3P1P2/2PBBN2/PP2Q1PP/R3K2R w KQ - 0 10',
        'caption': 'French with opposite-side castling. Black castled QS with a closed center — time to storm. White pushes g4-g5 and f5; Black pushes a5-a4-b5. The closed d4-e5 chain means the center won\'t distract from the race.',
        'arrows': [
            chess.svg.Arrow(chess.G2, chess.G4, color='#ff0000cc'),
            chess.svg.Arrow(chess.A7, chess.A5, color='#0000ffcc'),
            chess.svg.Arrow(chess.B7, chess.B5, color='#0000ffcc'),
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# HTML TEMPLATE
# ═══════════════════════════════════════════════════════════════════════════════

def law_section(num, title, body, pos_key=None):
    """Generate HTML for one law."""
    diagram = ''
    if pos_key and pos_key in positions:
        p = positions[pos_key]
        svg = board_svg(p['fen'], 
                       arrows=p.get('arrows'),
                       squares=p.get('squares'))
        uri = svg_to_data_uri(svg)
        diagram = f'''
        <div class="diagram">
            <img src="{uri}" alt="Position"/>
            <p class="caption">{p['caption']}</p>
        </div>
        '''
    
    return f'''
    <div class="law">
        <h2>LAW {num}: {title}</h2>
        <div class="law-content">
            <div class="law-text">{body}</div>
            {diagram}
        </div>
    </div>
    '''


html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@page {{
    size: A4;
    margin: 20mm 18mm;
    @bottom-center {{
        content: counter(page);
        font-size: 9pt;
        color: #666;
    }}
}}

body {{
    font-family: 'DejaVu Sans', 'Noto Sans', Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.5;
    color: #1a1a1a;
}}

h1 {{
    text-align: center;
    font-size: 22pt;
    color: #8b0000;
    margin-bottom: 5px;
    letter-spacing: 2px;
}}

.subtitle {{
    text-align: center;
    font-size: 11pt;
    color: #666;
    margin-bottom: 8px;
}}

.date {{
    text-align: center;
    font-size: 9pt;
    color: #999;
    margin-bottom: 25px;
}}

.intro {{
    background: #f8f0e8;
    border-left: 4px solid #8b0000;
    padding: 12px 16px;
    margin-bottom: 20px;
    font-style: italic;
    font-size: 10pt;
}}

.law {{
    margin-bottom: 22px;
    page-break-inside: avoid;
}}

h2 {{
    font-size: 13pt;
    color: #8b0000;
    border-bottom: 2px solid #8b0000;
    padding-bottom: 4px;
    margin-bottom: 10px;
}}

.law-content {{
    display: block;
}}

.law-text {{
    font-size: 10.5pt;
    margin-bottom: 10px;
}}

.law-text p {{
    margin: 6px 0;
}}

.key {{
    font-weight: bold;
    color: #8b0000;
}}

.diagram {{
    text-align: center;
    margin: 10px auto;
    page-break-inside: avoid;
}}

.diagram img {{
    width: 240px;
    height: 240px;
    border: 1px solid #ccc;
}}

.caption {{
    font-size: 9pt;
    color: #555;
    font-style: italic;
    margin-top: 4px;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.3;
}}

.personal {{
    background: #f0f4f8;
    border-left: 4px solid #2c5282;
    padding: 12px 16px;
    margin-top: 20px;
    page-break-inside: avoid;
}}

.personal h2 {{
    color: #2c5282;
    border-bottom-color: #2c5282;
}}

.summary {{
    background: #1a1a1a;
    color: #fff;
    padding: 16px 20px;
    margin-top: 20px;
    page-break-inside: avoid;
}}

.summary h2 {{
    color: #ff6b6b;
    border-bottom-color: #ff6b6b;
    margin-top: 0;
}}

.summary ul {{
    margin: 8px 0;
    padding-left: 20px;
}}

.summary li {{
    margin: 4px 0;
    color: #ddd;
}}

ul {{
    margin: 6px 0;
    padding-left: 22px;
}}

li {{
    margin: 3px 0;
}}
</style>
</head>
<body>

<h1>⚔️ THE IRON LAWS OF<br/>OPPOSITE-SIDE CASTLING</h1>
<p class="subtitle">A Strategic Framework for Mutual Attacks</p>
<p class="date">{today} — Prepared from the current concept notes</p>

<div class="intro">
When both kings castle on opposite wings, the game transforms from a positional 
battle into a race. These laws govern that race. Internalize them, and you'll know 
— move by move — whether you're winning the sprint or falling behind.
</div>

{law_section('I', 'THE RACE IS REAL — COUNT TEMPI',
    """<p>It's a mutual attack. You're not building a position — you're <span class="key">racing</span>. 
    Before committing, ask: <em>"Am I faster?"</em></p>
    <p>Count the moves to a breakthrough on both sides. If you're behind, you need to either 
    accelerate your attack or throw a wrench into theirs. If you can't do either, reconsider 
    whether OSC was the right choice.</p>
    <p><span class="key">Practical count:</span> How many pawn moves until I open a file? 
    How many until they do? Add piece deployment moves. Whoever's number is smaller is winning the race.</p>""",
    'race')}

{law_section('II', 'PAWNS STORM, PIECES FOLLOW',
    """<p>Push pawns toward their king <em>first</em>. Pawns open files. Pieces can't attack 
    a castled king through a closed pawn wall — they need doors.</p>
    <p><span class="key">The storm creates the doors. The pieces walk through.</span></p>
    <p>Typical pattern: advance 2–3 pawns toward their king, force a file open, then pour 
    rooks and queen down the open line. Don't bring pieces up first — they'll just stand 
    there with no entry points.</p>""",
    'pawns_storm')}

{law_section('III', 'YOUR PAWNS HAVE TWO JOBS — KNOW WHICH IS WHICH',
    """<p>Pawns near your king = <span class="key">SHIELDS</span> (DO NOT PUSH THEM).<br/>
    Pawns near their king = <span class="key">WEAPONS</span> (PUSH THEM HARD).</p>
    <p>This is why OSC is so double-edged: the pawns you want to attack with are on the opposite 
    side from the pawns you need for defense. If you push the wrong ones, you strip your own king.</p>
    <p><span class="key">Test:</span> Before pushing any pawn, ask: "Is this pawn currently 
    protecting my king?" If yes, it stays put unless you have a forced win.</p>""",
    'two_jobs')}

{law_section('IV', 'OPEN FILES ARE OXYGEN',
    """<p>The whole point of the pawn storm is to <span class="key">rip open files</span>. 
    An open file pointing at their king with your rook behind it is the most dangerous 
    structure in chess. Two open files = usually decisive.</p>
    <p>Prioritize the file opening over the pawn itself. Sacrificing a pawn to open a file 
    is almost always correct in OSC.</p>
    <p><span class="key">Corollary:</span> A half-open file you already have is worth more 
    than a full storm you haven't started. Use what's already there before investing 
    tempi in new fronts.</p>""",
    'open_files')}

{law_section('V', 'THE CENTER DECIDES THE RULES',
    """<p>The state of the center determines whether your storm even works:</p>
    <ul>
        <li><span class="key">Closed center:</span> Pawn storms work. You have time. Classical OSC. This is your ideal scenario.</li>
        <li><span class="key">Open center:</span> Pawn storms are too slow. The game is decided by piece activity and central tactics. Whoever controls the open center files often wins before any storm arrives.</li>
        <li><span class="key">Semi-open center:</span> Most dangerous. The center can blow open at any moment, and whoever is caught mid-storm with an exposed king loses.</li>
    </ul>
    <p><span class="key">For the French player:</span> The French often creates a closed or semi-closed center — 
    that's ideal for OSC storms. But if your opponent opens the center with a well-timed break, 
    your storm can become irrelevant overnight.</p>""",
    'center')}

{law_section('VI', "DON'T TRADE ATTACKING PIECES",
    """<p>In the race, your attacking pieces are irreplaceable. Don't trade your active bishop 
    for their passive one. Don't simplify unless it opens a decisive file.</p>
    <p><span class="key">Every piece trade favors the defender.</span> Fewer attackers = slower 
    attack = their counter-attack catches up.</p>
    <p><span class="key">Exception:</span> Trade pieces that <em>defend</em> their king. A bishop 
    or knight shielding their castled position? Kill it, even at material cost. That's not simplifying — 
    that's removing a wall.</p>""",
    'dont_trade')}

{law_section('VII', 'ONE TEMPO FOR DEFENSE CAN SAVE THREE',
    """<p>Pure aggression is a trap. Sometimes one prophylactic move — <span class="key">Kb1</span> 
    to tuck the king in the corner, <span class="key">a3</span> to prevent Nb4 — saves you from 
    having to spend 3 defensive moves later.</p>
    <p><span class="key">The iron test:</span> "If I ignore their threat and push my attack 
    one more move, do I win first?" If YES → ignore it and attack. If NO → spend the tempo now.</p>
    <p>The Kb1 move is particularly important: it removes back-rank tricks, gets off the c-file 
    (where Black's rook often arrives), and costs almost nothing.</p>""",
    'prophylaxis')}

{law_section('VIII', 'ROOKS BEFORE QUEENS',
    """<p>Counterintuitive, but: get your rooks to the open/semi-open files <em>before</em> 
    you bring your queen forward.</p>
    <p>The queen leading the attack is a <span class="key">target</span> — she can be harassed 
    with tempo-gaining threats. Rooks on open files are harder to challenge and create 
    permanent pressure.</p>
    <p><span class="key">Pattern:</span> Rooks to open files → create threats → queen comes 
    last as the finishing blow. The queen is the executioner, not the scout.</p>""",
    'rooks_before_queen')}

{law_section('IX', "KNOW WHEN YOU'RE LOSING — AND HIT THE BRAKE",
    """<p>If their storm is faster, you have three emergency options:</p>
    <ul>
        <li><span class="key">Counterattack in the center</span> — blow it open and change the nature of the game entirely</li>
        <li><span class="key">Blockade their storm</span> — place pieces where their pawns want to go</li>
        <li><span class="key">Trade queens</span> — no queens = no mating attack = their storm becomes meaningless pawn pushes</li>
    </ul>
    <p>Option 3 is your <span class="key">emergency brake</span>. Never be too proud to offer 
    a queen trade when you're losing the race. A queenless middlegame with a pawn storm 
    is just a slightly better endgame — not a mating attack.</p>""",
    'queen_trade')}

{law_section('X', 'THE FRENCH OSC — YOUR BATTLEFIELD',
    """<p>The French Defense is <em>built</em> for opposite-side castling. The closed center 
    (d4-e5 chain) gives both sides time to storm. Here's how the laws apply:</p>
    <ul>
        <li><span class="key">As Black (O-O-O):</span> Storm with g5-h5-g4. Your dark-squared 
        bishop on d6 supports the storm. The knight goes to f5 or e4 to attack d4 AND support the 
        kingside push.</li>
        <li><span class="key">As White (O-O) vs Black's O-O-O:</span> Storm with a4-b4-a5, open 
        the a/b files, swing rooks over. The Bg5 pin on f6 doubles as storm support.</li>
        <li><span class="key">Center break alert:</span> If Black plays ...f6 or ...cxd4, the 
        center opens — storms may become irrelevant. Be ready to shift to central play.</li>
    </ul>""",
    'french_osc')}

<div class="personal">
<h2>NOTE FOR DASH</h2>
<p>Your natural preference for closed positions and patient setups is actually an 
<strong>advantage</strong> in OSC — because the French gives you closed centers where 
storms have time to develop.</p>
<p>The adjustment you need is <strong>mental</strong>: once you castle opposite sides, 
the game clock changes. You're not building anymore — you're attacking. Every "setup" 
move that isn't directly advancing your storm or addressing their threats is a wasted tempo.</p>
<p><strong>The position is already built. Now execute.</strong></p>
</div>

<div class="summary">
<h2>QUICK REFERENCE — THE 10 IRON LAWS</h2>
<ul>
    <li><strong>I.</strong> The race is real — count tempi on both sides</li>
    <li><strong>II.</strong> Pawns storm first, pieces follow through the gaps</li>
    <li><strong>III.</strong> Shield pawns stay put, weapon pawns push hard</li>
    <li><strong>IV.</strong> Open files are oxygen — sacrifice pawns to get them</li>
    <li><strong>V.</strong> Closed center = storm works; open center = piece play wins</li>
    <li><strong>VI.</strong> Don't trade attackers; DO trade their defenders</li>
    <li><strong>VII.</strong> One prophylactic tempo now saves three defensive moves later</li>
    <li><strong>VIII.</strong> Rooks to files first, queen finishes</li>
    <li><strong>IX.</strong> Losing the race? Trade queens — emergency brake</li>
    <li><strong>X.</strong> The French center is your friend — keep it closed and storm</li>
</ul>
</div>

</body>
</html>'''

# Generate PDF
from pathlib import Path
out_path = Path(__file__).resolve().parents[2] / 'generated' / 'iron-laws-osc.pdf'
out_path.parent.mkdir(parents=True, exist_ok=True)
weasyprint.HTML(string=html).write_pdf(str(out_path))
print(f'Generated {out_path}')

import os
print(f'Size: {os.path.getsize(out_path):,} bytes')
