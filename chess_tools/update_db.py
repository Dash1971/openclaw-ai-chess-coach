#!/usr/bin/env python3
"""
Update chess-db/games.pgn from lichess studies.

Usage:
    python3 update_db.py                     # Update all studies in sources.txt
    python3 update_db.py STUDY_ID [ID2 ...]  # Update specific studies only

Compares by ChapterURL. Replaces updated annotations, adds new games.
Prints a summary of changes.
"""

import sys
import os
import re
import subprocess
import tempfile
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GAMES_PGN = os.path.join(SCRIPT_DIR, "games.pgn")
SOURCES_TXT = os.path.join(SCRIPT_DIR, "sources.txt")


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


def main():
    # Determine which studies to update
    if len(sys.argv) > 1:
        study_ids = sys.argv[1:]
    else:
        with open(SOURCES_TXT) as f:
            study_ids = [line.strip() for line in f if line.strip()]
    
    # Load current database
    with open(GAMES_PGN) as f:
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
        backup = GAMES_PGN + ".bak"
        with open(backup, 'w') as f:
            f.write(db_text)
        print(f"\nBackup saved to {backup}")
        
        # Rebuild in order
        output_parts = []
        for url in db_order:
            if url in db_by_url:
                output_parts.append(db_by_url[url]['full_text'].strip())
        
        with open(GAMES_PGN, 'w') as f:
            f.write('\n\n\n'.join(output_parts) + '\n')
        
        new_games = parse_pgn_to_games(open(GAMES_PGN).read())
        print(f"\nDatabase updated: {len(new_games)} games")
        print(f"Total: {total_new} new, {total_updated} updated, {total_unchanged} unchanged")
    else:
        print(f"\nNo changes detected. Database unchanged.")


if __name__ == "__main__":
    main()
