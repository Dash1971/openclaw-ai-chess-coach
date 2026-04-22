#!/usr/bin/env python3
import re
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


def main():
    paths = [
        Path('chess-db/external/wonestall-final-white-part1.pgn'),
        Path('chess-db/external/wonestall-final-white-part2.pgn'),
        Path('chess-db/external/wonestall-final-black-part1.pgn'),
        Path('chess-db/external/wonestall-final-black-part2.pgn'),
    ]
    for path in paths:
        text = path.read_text()
        sanitized = sanitize_text(text)
        out = path.with_stem(path.stem + '-sanitized')
        out.write_text(sanitized)
        print(out)


if __name__ == '__main__':
    main()
