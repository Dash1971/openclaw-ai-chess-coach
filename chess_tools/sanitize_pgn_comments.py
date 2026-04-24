#!/usr/bin/env python3
"""Sanitize PGN comment blocks.

Splits each { ... } comment into a directives block (clock, eval, etc.) and a
text block so engines and viewers do not choke on mixed content.

Usage:
    python3 sanitize_pgn_comments.py game1.pgn game2.pgn ...
    python3 sanitize_pgn_comments.py *.pgn --suffix -clean
    python3 sanitize_pgn_comments.py *.pgn --output-dir /tmp/sanitized

Each input file is written as a sibling with the suffix appended to the stem
(default: -sanitized) unless --output-dir is given, in which case the file is
placed in that directory instead.
"""

import argparse
import re
import sys
from pathlib import Path

DIRECTIVE_RE = re.compile(r'\[%[^\]]+\]')
COMMENT_RE = re.compile(r'\{([^{}]*)\}', re.S)


def sanitize_comment_body(body: str) -> str:
    s = body.strip()
    if not s:
        return '{ }'

    directives = DIRECTIVE_RE.findall(s)
    text = DIRECTIVE_RE.sub('', s)
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()

    if not directives:
        return '{ ' + s + ' }'

    directive_block = ' '.join(directives).strip()
    parts = []
    if directive_block:
        parts.append('{ ' + directive_block + ' }')
    if text:
        parts.append('{ ' + text + ' }')
    return ' '.join(parts)


def sanitize_text(text: str) -> str:
    out = []
    last = 0
    for m in COMMENT_RE.finditer(text):
        out.append(text[last:m.start()])
        out.append(sanitize_comment_body(m.group(1)))
        last = m.end()
    out.append(text[last:])
    return ''.join(out)


def output_path(src: Path, suffix: str, output_dir: Path | None) -> Path:
    name = src.stem + suffix + src.suffix
    if output_dir is not None:
        return output_dir / name
    return src.parent / name


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Sanitize PGN comment blocks (split directives from text).',
    )
    parser.add_argument(
        'pgn', nargs='+', type=Path,
        metavar='PGN',
        help='One or more PGN files to sanitize.',
    )
    parser.add_argument(
        '--suffix', default='-sanitized',
        help='Suffix appended to each output stem (default: -sanitized).',
    )
    parser.add_argument(
        '--output-dir', type=Path, default=None,
        metavar='DIR',
        help='Write output files to DIR instead of alongside each input.',
    )
    args = parser.parse_args(argv)

    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    errors = 0
    for src in args.pgn:
        if not src.exists():
            print(f'error: {src}: file not found', file=sys.stderr)
            errors += 1
            continue
        text = src.read_text()
        sanitized = sanitize_text(text)
        out = output_path(src, args.suffix, args.output_dir)
        out.write_text(sanitized)
        print(out)

    if errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
