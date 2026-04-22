#!/usr/bin/env python3
"""Chess diagram helpers for PDF generators. Uses python-chess SVG rendering."""

import chess
import chess.svg
import base64


def board_svg(fen, size=240, arrows=None, flipped=False):
    """Generate SVG of a chess position."""
    board = chess.Board(fen)
    kwargs = {'size': size, 'flipped': flipped}
    if arrows:
        kwargs['arrows'] = arrows
    return chess.svg.board(board, **kwargs)


def svg_to_data_uri(svg_str):
    """Convert SVG string to base64 data URI for HTML embedding."""
    b64 = base64.b64encode(svg_str.encode()).decode()
    return f'data:image/svg+xml;base64,{b64}'


def diagram_html(fen, caption, arrows=None, size=240, flipped=False):
    """Return complete HTML div with chess diagram and caption."""
    svg = board_svg(fen, size, arrows, flipped=flipped)
    uri = svg_to_data_uri(svg)
    return f'''<div class="diagram">
    <img src="{uri}" alt="Position"/>
    <p class="caption">{caption}</p>
</div>'''


# CSS to include in the PDF stylesheet
DIAGRAM_CSS = '''
.diagram {
    text-align: center;
    margin: 10px auto;
    page-break-inside: avoid;
}

.diagram img {
    width: 240px;
    height: 240px;
    border: 1px solid #ccc;
}

.caption {
    font-size: 9px;
    color: #555;
    font-style: italic;
    margin-top: 4px;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.3;
}

.diagram-pair {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 10px auto;
    page-break-inside: avoid;
}

.diagram-pair .diagram {
    margin: 0;
}

.diagram-pair .diagram img {
    width: 200px;
    height: 200px;
}
'''
