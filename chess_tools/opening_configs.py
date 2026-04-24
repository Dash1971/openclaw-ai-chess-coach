#!/usr/bin/env python3
"""Opening guide registry for generic opening-tag/guide commands.

Script paths (tag_script, guide_script) are resolved relative to this file so
the tools can be invoked from any working directory.  Output path defaults
(default_tag_output, default_pdf_output) are cwd-relative or /tmp so that
derived files are never written into the source tree by default.  Override them
with --output / --db CLI flags or the OPENING_* environment variables.
"""

from __future__ import annotations

from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent

OPENING_CONFIGS = {
    "stonewall": {
        "id": "stonewall",
        "title": "Stonewall",
        "description": "Stonewall Dutch guide/tag pipeline.",
        "tag_script": _SCRIPTS / "tag_games.py",
        "guide_script": _SCRIPTS / "generate_pdf.py",
        "default_tag_output": Path("/tmp/sw_data.json"),
        "default_pdf_output": Path("stonewall-cheatsheet.pdf"),
        "default_html_debug": Path("/tmp/stonewall_cheatsheet.html"),
    },
    "french": {
        "id": "french",
        "title": "French Defense",
        "description": "French Defense guide/tag pipeline.",
        "tag_script": _SCRIPTS / "tag_french.py",
        "guide_script": _SCRIPTS / "generate_french_pdf.py",
        "default_tag_output": Path("/tmp/french_data.json"),
        "default_pdf_output": Path("french-cheatsheet.pdf"),
        "default_html_debug": Path("/tmp/french_cheatsheet.html"),
    },
}


def get_opening_config(opening: str) -> dict:
    key = opening.strip().lower()
    if key not in OPENING_CONFIGS:
        valid = ", ".join(sorted(OPENING_CONFIGS))
        raise KeyError(f"Unknown opening '{opening}'. Valid openings: {valid}")
    return OPENING_CONFIGS[key]


def list_openings() -> list[dict]:
    return [OPENING_CONFIGS[k] for k in sorted(OPENING_CONFIGS)]

