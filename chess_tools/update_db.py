#!/usr/bin/env python3
"""Update a PGN corpus from one or more Lichess studies.

Compares by ChapterURL. Replaces updated annotations, adds new games,
and preserves game order where possible.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import time
from pathlib import Path

DEFAULT_GAMES_PGN = Path("games.pgn")
DEFAULT_SOURCES_TXT = Path("sources.txt")


def parse_pgn_to_games(text):
    """Parse PGN text into list of games, each as dict with headers, full_text, chapter_url."""
    games = []
    lines = text.split('\n')
    current_lines = []
    current_headers = {}
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Header line
        m = re.match(r'\[(\w+)\s+"(.*)"\]', line)
        if m:
            if not current_lines:
                # Starting a new game
                pass
            current_headers[m.group(1)] = m.group(2)
            current_lines.append(line)
            i += 1
            continue
        
        # Blank line or move text
        current_lines.append(line)
        
        # Check if this is a result line (game ended)
        stripped = line.strip()
        if current_headers and stripped and re.search(r'(?:1-0|0-1|1/2-1/2|\*)\s*$', stripped):
            # Game complete
            games.append({
                'headers': dict(current_headers),
                'full_text': '\n'.join(current_lines),
                'chapter_url': current_headers.get('ChapterURL', ''),
            })
            current_headers = {}
            current_lines = []
        
        i += 1
    
    # Handle any remaining game (no result line at end)
    if current_headers and current_lines:
        games.append({
            'headers': dict(current_headers),
            'full_text': '\n'.join(current_lines),
            'chapter_url': current_headers.get('ChapterURL', ''),
        })
    
    return games


def download_study(study_id):
    """Download PGN from lichess study API. Returns text or None."""
    url = f"https://lichess.org/api/study/{study_id}.pgn"
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "30", url],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
        else:
            print(f"  ERROR: Failed to download {study_id}")
            return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update a PGN corpus from one or more Lichess studies.")
    parser.add_argument("study_ids", nargs="*", help="Optional Lichess study ids to update explicitly")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_GAMES_PGN),
        help="Path to the target PGN database (default: ./games.pgn)",
    )
    parser.add_argument(
        "--sources",
        default=str(DEFAULT_SOURCES_TXT),
        help="Path to a text file containing one Lichess study id per line (default: ./sources.txt)",
    )
    return parser


def main(argv: list[str] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    games_pgn = Path(args.db)
    sources_txt = Path(args.sources)

    if args.study_ids:
        study_ids = args.study_ids
    else:
        if not sources_txt.exists():
            raise SystemExit(
                f"Sources file not found: {sources_txt}\n"
                "Pass explicit study ids or provide --sources <sources.txt>."
            )
        with open(sources_txt) as f:
            study_ids = [line.strip() for line in f if line.strip()]

    if not study_ids:
        raise SystemExit("No study ids provided. Pass study ids directly or via --sources.")

    if not games_pgn.exists():
        raise SystemExit(
            f"PGN database not found: {games_pgn}\n"
            "Create an initial PGN file or point --db at an existing corpus."
        )

    with open(games_pgn) as f:
        db_text = f.read()

    db_games = parse_pgn_to_games(db_text)
    print(f"Current database: {len(db_games)} games")
    
    # Index by ChapterURL
    db_by_url = {}
    db_order = []  # preserve order
    for g in db_games:
        url = g['chapter_url']
        db_by_url[url] = g
        db_order.append(url)
    
    total_new = 0
    total_updated = 0
    total_unchanged = 0
    
    for study_id in study_ids:
        print(f"\n--- Study: {study_id} ---")
        fresh_text = download_study(study_id)
        if not fresh_text:
            continue
        
        fresh_games = parse_pgn_to_games(fresh_text)
        print(f"  Fresh: {len(fresh_games)} games")
        
        new_count = 0
        updated_count = 0
        unchanged_count = 0
        
        for fg in fresh_games:
            url = fg['chapter_url']
            if not url:
                continue
            
            if url not in db_by_url:
                # New game — append
                db_by_url[url] = fg
                db_order.append(url)
                new_count += 1
                chapter = fg['headers'].get('ChapterName', 'unknown')
                print(f"  NEW: {chapter}")
            else:
                # Compare content
                old_text = db_by_url[url]['full_text'].strip()
                new_text = fg['full_text'].strip()
                if old_text != new_text:
                    db_by_url[url] = fg
                    updated_count += 1
                    chapter = fg['headers'].get('ChapterName', 'unknown')
                    diff = len(new_text) - len(old_text)
                    print(f"  UPDATED: {chapter} ({diff:+d} chars)")
                else:
                    unchanged_count += 1
        
        print(f"  Summary: {new_count} new, {updated_count} updated, {unchanged_count} unchanged")
        total_new += new_count
        total_updated += updated_count
        total_unchanged += unchanged_count
        
        time.sleep(1)  # Rate limit lichess API
    
    # Write updated database
    if total_new > 0 or total_updated > 0:
        # Backup
        backup = games_pgn.with_suffix(games_pgn.suffix + ".bak")
        with open(backup, 'w') as f:
            f.write(db_text)
        print(f"\nBackup saved to {backup}")
        
        # Rebuild in order
        output_parts = []
        for url in db_order:
            if url in db_by_url:
                output_parts.append(db_by_url[url]['full_text'].strip())
        
        with open(games_pgn, 'w') as f:
            f.write('\n\n\n'.join(output_parts) + '\n')

        with open(games_pgn) as f:
            new_games = parse_pgn_to_games(f.read())
        print(f"\nDatabase updated: {len(new_games)} games")
        print(f"Total: {total_new} new, {total_updated} updated, {total_unchanged} unchanged")
    else:
        print(f"\nNo changes detected. Database unchanged.")


if __name__ == "__main__":
    main()
