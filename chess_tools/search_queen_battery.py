#!/usr/bin/env python3
"""
Search for Aman's games with Qc2 (White) and Qc7 (Black) prophylactic moves
protecting bishops in battery setups.
"""

import re
from pathlib import Path

def parse_pgn_file(filepath):
    """Parse PGN file and return list of games with metadata."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Split by game headers
    games = []
    game_blocks = re.split(r'\n\n(?=\[Event )', content.strip())
    
    for block in game_blocks:
        if not block.strip():
            continue
        
        game = {'headers': {}, 'moves': ''}
        
        # Parse headers
        for match in re.finditer(r'\[(\w+)\s+"([^"]*)"\]', block):
            game['headers'][match.group(1)] = match.group(2)
        
        # Find moves section (after headers)
        lines = block.split('\n')
        in_moves = False
        move_lines = []
        for line in lines:
            if in_moves:
                move_lines.append(line)
            elif line.strip() and not line.strip().startswith('['):
                in_moves = True
                move_lines.append(line)
        
        game['moves'] = ' '.join(move_lines)
        games.append(game)
    
    return games

def find_queen_battery_patterns(games):
    """Find games with Qc2 (White) or Qc7 (Black) protecting bishop battery."""
    results = {
        'qc2_white': [],  # White plays Qc2
        'qc7_black': []   # Black plays Qc7
    }
    
    for game in games:
        # Only Aman's games (wonestall or sterkurstrakur)
        white = game['headers'].get('White', '')
        black = game['headers'].get('Black', '')
        
        is_amam_white = 'wonestall' in white.lower() or 'sterkurstrakur' in white.lower()
        is_amam_black = 'wonestall' in black.lower() or 'sterkurstrakur' in black.lower()
        
        moves = game['moves'].lower()
        
        # Look for Qc2 when Aman is White
        if is_amam_white and 'qc2' in moves:
            # Check if there's bishop tension context
            # Pattern: bishop on b1-h7 diagonal (Be2, Bd3, Bc4) and Qc2
            if any(b in moves for b in ['be2', 'bd3', 'bc4', 'bb5']):
                results['qc2_white'].append({
                    'event': game['headers'].get('Event', 'Unknown'),
                    'white': white,
                    'black': black,
                    'result': game['headers'].get('Result', '*'),
                    'site': game['headers'].get('Site', ''),
                    'moves': game['moves'][:200]  # First 200 chars
                })
        
        # Look for Qc7 when Aman is Black  
        if is_amam_black and 'qc7' in moves:
            # Check if there's bishop tension context
            # Pattern: bishop on e6-h3 diagonal (Be7, Bd6, Be6) and Qc7
            if any(b in moves for b in ['bd6', 'be7', 'be6', 'bc5']):
                results['qc7_black'].append({
                    'event': game['headers'].get('Event', 'Unknown'),
                    'white': white,
                    'black': black,
                    'result': game['headers'].get('Result', '*'),
                    'site': game['headers'].get('Site', ''),
                    'moves': game['moves'][:200]
                })
    
    return results

if __name__ == '__main__':
    pgn_file = str(Path(__file__).resolve().parent / 'games.pgn')
    
    print("Parsing PGN file...")
    games = parse_pgn_file(pgn_file)
    print(f"Found {len(games)} games")
    
    print("\nSearching for Qc2/Qc7 battery patterns...")
    results = find_queen_battery_patterns(games)
    
    print(f"\n=== Qc2 (White Stonewall) - {len(results['qc2_white'])} games ===")
    for i, game in enumerate(results['qc2_white'][:10], 1):
        print(f"\n{i}. {game['white']} vs {game['black']} ({game['result']})")
        print(f"   Event: {game['event']}")
        print(f"   Site: {game['site']}")
        print(f"   Moves: {game['moves']}...")
    
    print(f"\n=== Qc7 (Black Stonewall) - {len(results['qc7_black'])} games ===")
    for i, game in enumerate(results['qc7_black'][:10], 1):
        print(f"\n{i}. {game['white']} vs {game['black']} ({game['result']})")
        print(f"   Event: {game['event']}")
        print(f"   Site: {game['site']}")
        print(f"   Moves: {game['moves']}...")
