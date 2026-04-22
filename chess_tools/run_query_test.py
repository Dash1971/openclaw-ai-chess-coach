#!/usr/bin/env python3
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent

def run_query(query_file):
    result = subprocess.run(
        ["python3", "query_cli.py", "--query-file", query_file, "--pretty"],
        capture_output=True,
        text=True,
        cwd=str(BASE)
    )
    return result.stdout + result.stderr

queries = [
    ("queen_rook_battery_hfile.json", "Queen-Rook battery with checkmate"),
    ("queen_rook_hfile.json", "Q+R stacked on h-file"),
    ("queen_stacked_rooks_h.json", "Queen and stacked rooks on h-file")
]

for query_file, desc in queries:
    print(f"\n{'='*60}")
    print(f"Query: {desc}")
    print(f"File: {query_file}")
    print(f"{'='*60}")
    output = run_query(query_file)
    print(output)
