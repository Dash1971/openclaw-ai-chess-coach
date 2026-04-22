#!/usr/bin/env python3
"""Natural-language wrapper for chess-db structured queries.

Rule-first approach:
- detect whether the user wants exact vs fuzzy search
- extract anchors (moves, squares, players, colors, study hints)
- compile into exact/fuzzy JSON for query_cli/query_engine
- refuse underspecified prompts instead of inventing false precision
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Any

HEAVY_PIECE_REGEX = r"(?:Q|R)[a-h1-8x]*[a-h][1-8][+#]?"
ANY_ATTACKING_FOLLOWUP_REGEX = r"(?:Q|R)[a-h1-8x]*[a-h][1-8][+#]?|[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8][+#]?"

from query_engine import DB_PATH, QueryError
from query_fuzzy import run_fuzzy_query
from query_engine import run_query

PIECE_WORDS = {
    "pawn": "P",
    "knight": "N",
    "bishop": "B",
    "rook": "R",
    "queen": "Q",
    "king": "K",
}

PLAYER_ALIASES = {
    "wonestall": "wonestall",
    "sterkurstrakur": "sterkurstrakur",
    "habitual": "habitual",
    "aman": "aman",
}

STUDY_HINTS = {
    "stonewall": {"study_contains": "Stonewall"},
    "french": {"study_contains": "French"},
    "habits": {"study_contains": "Habits"},
    "london": {"opening_contains": "London"},
}

FUZZY_HINTS = [
    "similar",
    "closest",
    "analogue",
    "analogous",
    "same idea",
    "same concept",
    "like this",
    "motif",
    "pattern",
    "kind of",
]

EXACT_HINTS = [
    "exact",
    "exactly",
    "literal",
    "literally",
    "only true examples",
    "where exactly",
    "actual examples",
    "only actual",
]

SAN_RE = re.compile(
    r"\b(?:O-O-O|O-O|[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?[+#]?|[KQRBN][a-h]?[1-8]?|[a-h]x[a-h][1-8](?:=[QRBN])?[+#]?)\b"
)


@dataclass
class ParsedPrompt:
    raw_text: str
    mode: str
    player: str | None
    color: str | None
    filters: dict[str, Any]
    moves: list[str]
    square_facts: list[dict[str, Any]]
    move_windows: list[int | None]
    battery_hint: bool
    defend_hint: bool
    motif_templates: list[dict[str, Any]]
    sequence_templates: list[dict[str, Any]]
    clarification_needed: str | None


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def infer_mode(text: str, forced: str | None = None) -> str:
    if forced in {"exact", "fuzzy"}:
        return forced
    low = text.lower()
    if any(h in low for h in EXACT_HINTS):
        return "exact"
    if any(h in low for h in FUZZY_HINTS):
        return "fuzzy"
    return "exact"


def infer_player(text: str, explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    low = text.lower()
    hits = [canonical for alias, canonical in PLAYER_ALIASES.items() if alias in low]
    if not hits:
        return None
    if "aman" in hits:
        if "french" in low:
            return "sterkurstrakur"
        if "stonewall" in low:
            return "wonestall"
        if "habits" in low:
            return "habitual"
        return None
    return hits[0]


def infer_color(text: str, explicit: str | None = None) -> str | None:
    if explicit in {"white", "black"}:
        return explicit
    low = text.lower()
    if re.search(r"\bas black\b|\bblack games\b|\bblack side\b", low):
        return "black"
    if re.search(r"\bas white\b|\bwhite games\b|\bwhite side\b", low):
        return "white"
    return None


def infer_filters(text: str) -> dict[str, Any]:
    low = text.lower()
    filters: dict[str, Any] = {}
    for needle, patch in STUDY_HINTS.items():
        if needle in low:
            filters.update(patch)
    return filters


def extract_moves(text: str) -> list[str]:
    moves: list[str] = []
    for match in SAN_RE.finditer(text):
        token = match.group(0).strip(".,;:()[]{}")
        if token.lower() in {"as", "is", "on", "in", "of", "to"}:
            continue
        if re.fullmatch(r"[a-h][1-8]", token):
            prefix = text[max(0, match.start() - 60):match.start()].lower()
            if (
                re.search(r"(?:pawn|knight|bishop|rook|queen|king)\s+on\s*$", prefix)
                or re.search(r"(?:white|black|my|our|their|enemy|opponent|opp)\s+(?:pawn|knight|bishop|rook|queen|king)\s+on\s*$", prefix)
                or re.search(r"bishop\s+(?:point(?:ed)?|aim(?:ing)?|eye(?:ing)?)\s+at\s*$", prefix)
                or re.search(r"knight\s+outpost\s+on\s*$", prefix)
                or re.search(r"battery\s+toward\s*$", prefix)
                or re.search(r"pin(?:ned)?\s+to\s+(?:king|queen)\s+on\s*$", prefix)
                or re.search(r"pawn\s+storm\s+against\s+(?:king|queen)side\s+castled\s+king\s*$", prefix)
                or re.search(r"(?:bishop|rook)\s+sac(?:rifice)?\s+on\s*$", prefix)
                or re.search(r"rook\s+swing\s+to\s*$", prefix)
            ):
                continue
        if token and token not in moves:
            moves.append(token)
    return moves


def color_word_to_spec(word: str | None) -> str:
    if not word:
        return "any"
    word = word.lower()
    if word in {"white", "black"}:
        return word
    if word in {"my", "our", "self"}:
        return "self"
    if word in {"their", "enemy", "opponent", "opp"}:
        return "opponent"
    return "any"


def extract_square_facts(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"\b(?:(white|black|my|our|their|enemy|opponent|opp)\s+)?"
        r"(pawn|knight|bishop|rook|queen|king)\s+on\s+([a-h][1-8])\b",
        re.IGNORECASE,
    )
    facts = []
    for match in pattern.finditer(text):
        color_word, piece_word, square = match.groups()
        prefix = text[max(0, match.start() - 30):match.start()].lower()
        if re.search(r"pin(?:ned)?\s+to\s*$", prefix):
            continue
        facts.append(
            {
                "color": color_word_to_spec(color_word),
                "piece": PIECE_WORDS[piece_word.lower()],
                "square": square.lower(),
            }
        )
    return facts


def extract_move_windows(text: str, move_count: int) -> list[int | None]:
    windows: list[int | None] = [None] * move_count
    low = text.lower()

    ply_match = re.search(r"within\s+(\d+)\s+pl(?:y|ies)", low)
    move_match = re.search(r"within\s+(\d+)\s+move(?:s)?", low)
    window = None
    if ply_match:
        window = int(ply_match.group(1))
    elif move_match:
        window = int(move_match.group(1)) * 2
    elif any(word in low for word in ["then", "followed by", "before", "after"]):
        window = 6

    if window is not None:
        for i in range(1, move_count):
            windows[i] = window
    return windows


def extract_battery_hint(text: str) -> bool:
    low = text.lower()
    return any(word in low for word in ["battery", "x-ray", "xray", "queen behind bishop"])


def extract_defend_hint(text: str) -> bool:
    low = text.lower()
    return any(word in low for word in ["defend", "protect", "stabilize", "support"])


def infer_template_window(low: str, default_plies: int) -> int:
    ply_match = re.search(r"within\s+(\d+)\s+pl(?:y|ies)", low)
    move_match = re.search(r"within\s+(\d+)\s+move(?:s)?", low)
    if ply_match:
        return int(ply_match.group(1))
    if move_match:
        return int(move_match.group(1)) * 2
    return default_plies


def extract_motif_templates(text: str) -> list[dict[str, Any]]:
    motifs: list[dict[str, Any]] = []
    low = text.lower()
    has_rook_lift_swing_combo = "rook lift" in low and "rook swing" in low
    has_bishop_sac_combo = bool(re.search(r"bishop\s+sac(?:rifice)?\s+on\s+[a-h][1-8]", low)) and (
        "attacking continuation" in low or "attack continuation" in low or "follow-up attack" in low or "follow up attack" in low or "continuation" in low
    )
    has_opp_castle_combo = (
        ("opposite-side castling" in low or "opposite side castling" in low)
        and "pawn storm" in low
        and (
            "heavy-piece follow-up" in low
            or "heavy piece follow-up" in low
            or "heavy-piece followup" in low
            or "heavy piece followup" in low
            or "heavy-piece follow up" in low
            or "heavy piece follow up" in low
        )
    )

    for color_word, file_letter in re.findall(
        r"\b(?:(white|black|my|our|their|enemy|opponent|opp)\s+)?rook lift(?: to the)? ([a-h])-file\b",
        text,
        flags=re.IGNORECASE,
    ):
        motifs.append(
            {
                "label": f"{color_word or 'any'} rook lift to {file_letter.lower()}-file",
                "required": True,
                "predicate": {
                    "type": "rook_lifted",
                    "phase": "before",
                    "color": color_word_to_spec(color_word),
                    "file": file_letter.lower(),
                    "min_advance": 2,
                },
            }
        )

    if not has_rook_lift_swing_combo and re.search(r"\brook lift\b", text, flags=re.IGNORECASE):
        motifs.append(
            {
                "label": "rook lift",
                "required": True,
                "predicate": {
                    "type": "rook_lifted",
                    "phase": "before",
                    "color": "any",
                    "min_advance": 2,
                },
            }
        )

    if not has_opp_castle_combo and re.search(r"\bopposite[- ]side castling\b", text, flags=re.IGNORECASE):
        motifs.append(
            {
                "label": "opposite-side castling",
                "required": True,
                "predicate": {
                    "type": "opposite_side_castling",
                    "phase": "before",
                },
            }
        )

    for color_word, file_letter in re.findall(
        r"\b(?:(white|black|my|our|their|enemy|opponent|opp)\s+)?rook on (?:an? )?open ([a-h])-?file\b",
        text,
        flags=re.IGNORECASE,
    ):
        motifs.append(
            {
                "label": f"{color_word or 'any'} rook on open {file_letter.lower()}-file",
                "required": True,
                "predicate": {
                    "type": "rook_on_open_file",
                    "phase": "before",
                    "color": color_word_to_spec(color_word),
                    "file": file_letter.lower(),
                },
            }
        )

    for color_word, target_square in re.findall(
        r"\b(?:(white|black|my|our|their|enemy|opponent|opp)\s+)?bishop (?:point(?:ed)?|aim(?:ing)?|eye(?:ing)?) at ([a-h][1-8])\b",
        text,
        flags=re.IGNORECASE,
    ):
        motifs.append(
            {
                "label": f"{color_word or 'any'} bishop attacks {target_square.lower()}",
                "required": True,
                "predicate": {
                    "type": "piece_attacks_square",
                    "phase": "before",
                    "color": color_word_to_spec(color_word),
                    "piece": "B",
                    "target_square": target_square.lower(),
                },
            }
        )

    for color_word, square in re.findall(
        r"\b(?:(white|black|my|our|their|enemy|opponent|opp)\s+)?knight outpost on ([a-h][1-8])\b",
        text,
        flags=re.IGNORECASE,
    ):
        motifs.append(
            {
                "label": f"{color_word or 'any'} knight outpost on {square.lower()}",
                "required": True,
                "predicate": {
                    "type": "knight_outpost",
                    "phase": "before",
                    "color": color_word_to_spec(color_word),
                    "square": square.lower(),
                },
            }
        )

    for color_word, target_square in re.findall(
        r"\b(?:(white|black|my|our|their|enemy|opponent|opp)\s+)?(?:queen[- ]bishop|bishop[- ]queen|queen and bishop) battery toward ([a-h][1-8])\b",
        text,
        flags=re.IGNORECASE,
    ):
        motifs.append(
            {
                "label": f"{color_word or 'any'} queen-bishop battery toward {target_square.lower()}",
                "required": True,
                "predicate": {
                    "type": "battery_toward_square",
                    "phase": "before",
                    "color": color_word_to_spec(color_word),
                    "back_piece": "Q",
                    "front_piece": "B",
                    "target_square": target_square.lower(),
                },
            }
        )

    for color_word, file_letter in re.findall(
        r"\b(?:(white|black|my|our|their|enemy|opponent|opp)\s+)?rook on (?:an? )?semi-open ([a-h])-?file\b",
        text,
        flags=re.IGNORECASE,
    ):
        motifs.append(
            {
                "label": f"{color_word or 'any'} rook on semi-open {file_letter.lower()}-file",
                "required": True,
                "predicate": {
                    "type": "rook_on_semi_open_file",
                    "phase": "before",
                    "color": color_word_to_spec(color_word),
                    "file": file_letter.lower(),
                },
            }
        )

    for pinned_color, piece_word, target_piece, square in re.findall(
        r"\b(?:(white|black|my|our|their|enemy|opponent|opp)\s+)?(pawn|knight|bishop|rook|queen) pinned to (king|queen) on ([a-h][1-8])\b",
        text,
        flags=re.IGNORECASE,
    ):
        motifs.append(
            {
                "label": f"{pinned_color or 'any'} {piece_word.lower()} pinned to {target_piece.upper()} on {square.lower()}",
                "required": True,
                "predicate": {
                    "type": "piece_pinned_to_target",
                    "phase": "before",
                    "pinned_color": color_word_to_spec(pinned_color),
                    "piece": PIECE_WORDS[piece_word.lower()],
                    "square": square.lower(),
                    "target_piece": target_piece.upper()[0],
                },
            }
        )

    for color_word, side_word in re.findall(
        r"\b(?:(white|black|my|our|their|enemy|opponent|opp)\s+)?pawn storm against (king|queen)side castled king\b",
        text,
        flags=re.IGNORECASE,
    ):
        if has_opp_castle_combo:
            continue
        motifs.append(
            {
                "label": f"{color_word or 'any'} pawn storm against {side_word.lower()}side king",
                "required": True,
                "predicate": {
                    "type": "pawn_storm_against_castled_king",
                    "phase": "before",
                    "color": color_word_to_spec(color_word),
                    "target_side": "king" if side_word.lower().startswith("king") else "queen",
                },
            }
        )

    for color_word, piece_word, square in re.findall(
        r"\b(?:(white|black|my|our|their|enemy|opponent|opp)\s+)?(bishop|rook) sac(?:rifice)? on ([a-h][1-8])\b",
        text,
        flags=re.IGNORECASE,
    ):
        if piece_word.lower() == "bishop" and has_bishop_sac_combo:
            continue
        piece_letter = PIECE_WORDS[piece_word.lower()]
        motifs.append(
            {
                "label": f"{color_word or 'any'} {piece_word.lower()} sac on {square.lower()}",
                "required": True,
                "move_template": {
                    "move": rf"{piece_letter}x{square.lower()}[+#]?",
                    "move_mode": "regex",
                    "move_by": color_word_to_spec(color_word) if color_word else "any",
                },
            }
        )

    for color_word, square in re.findall(
        r"\b(?:(white|black|my|our|their|enemy|opponent|opp)\s+)?rook swing to ([a-h][1-8])\b",
        text,
        flags=re.IGNORECASE,
    ):
        motifs.append(
            {
                "label": f"{color_word or 'any'} rook swing to {square.lower()}",
                "required": True,
                "move_template": {
                    "move": rf"R.?{square.lower()}[+#]?",
                    "move_mode": "regex",
                    "move_by": color_word_to_spec(color_word) if color_word else "any",
                },
            }
        )

    return motifs


def extract_sequence_templates(text: str) -> list[dict[str, Any]]:
    low = text.lower()
    templates: list[dict[str, Any]] = []

    has_rook_lift = "rook lift" in low
    has_rook_swing = "rook swing" in low
    if has_rook_lift and has_rook_swing:
        window = infer_template_window(low, default_plies=6)
        swing_square_match = re.search(r"rook swing to ([a-h][1-8])", low)
        swing_regex = rf"R.?{swing_square_match.group(1)}[+#]?" if swing_square_match else r"R[a-h1-8x]*[a-h][3-6][+#]?"
        templates.append(
            {
                "label": "rook lift -> rook swing",
                "steps": [
                    {
                        "label": "rook lift setup",
                        "move_by": "any",
                        "predicates": [
                            {
                                "type": "rook_lifted",
                                "phase": "before",
                                "color": "any",
                                "min_advance": 2,
                            }
                        ],
                    },
                    {
                        "label": "rook swing",
                        "move": swing_regex,
                        "move_mode": "regex",
                        "move_by": "any",
                        "within_plies": window,
                    },
                ],
            }
        )

    has_bishop_sac = bool(re.search(r"bishop\s+sac(?:rifice)?\s+on\s+[a-h][1-8]", low))
    has_attack_continuation = "attacking continuation" in low or "attack continuation" in low or "follow-up attack" in low or "follow up attack" in low or "continuation" in low
    if has_bishop_sac and has_attack_continuation:
        window = infer_template_window(low, default_plies=6)
        sac_square_match = re.search(r"bishop\s+sac(?:rifice)?\s+on\s+([a-h][1-8])", low)
        sac_square = sac_square_match.group(1) if sac_square_match else "h7"
        if "heavy-piece" in low or "heavy piece" in low or "queen" in low or "rook" in low:
            followup_regex = HEAVY_PIECE_REGEX
        elif "check" in low or "mate" in low:
            followup_regex = r".*[+#]"
        else:
            followup_regex = ANY_ATTACKING_FOLLOWUP_REGEX
        templates.append(
            {
                "label": "bishop sac -> attacking continuation",
                "steps": [
                    {
                        "label": f"bishop sac on {sac_square}",
                        "move": rf"Bx{sac_square}[+#]?",
                        "move_mode": "regex",
                        "move_by": "any",
                    },
                    {
                        "label": "attacking continuation",
                        "move": followup_regex,
                        "move_mode": "regex",
                        "move_by": "any",
                        "within_plies": window,
                    },
                ],
            }
        )

    has_opp_castle = "opposite-side castling" in low or "opposite side castling" in low
    has_pawn_storm = "pawn storm" in low
    has_heavy_followup = "heavy-piece follow-up" in low or "heavy piece follow-up" in low or "heavy-piece followup" in low or "heavy piece followup" in low or "heavy-piece follow up" in low or "heavy piece follow up" in low
    if has_opp_castle and has_pawn_storm and has_heavy_followup:
        storm_window = infer_template_window(low, default_plies=10)
        follow_window = infer_template_window(low, default_plies=6)
        target_side = None
        if "kingside" in low:
            target_side = "king"
        elif "queenside" in low:
            target_side = "queen"
        heavy_regex = HEAVY_PIECE_REGEX
        if "queen follow-up" in low or "queen follow up" in low:
            heavy_regex = r"Q[a-h1-8x]*[a-h][1-8][+#]?"
        elif "rook follow-up" in low or "rook follow up" in low:
            heavy_regex = r"R[a-h1-8x]*[a-h][1-8][+#]?"
        templates.append(
            {
                "label": "opposite-side castling + pawn storm + heavy-piece follow-up",
                "steps": [
                    {
                        "label": "opposite-side castling",
                        "move_by": "any",
                        "predicates": [
                            {
                                "type": "opposite_side_castling",
                                "phase": "before",
                            }
                        ],
                    },
                    {
                        "label": "pawn storm",
                        "move_by": "any",
                        "within_plies": storm_window,
                        "predicates": [
                            {
                                "type": "pawn_storm_against_castled_king",
                                "phase": "before",
                                "color": "any",
                                **({"target_side": target_side} if target_side else {}),
                            }
                        ],
                    },
                    {
                        "label": "heavy-piece follow-up",
                        "move": heavy_regex,
                        "move_mode": "regex",
                        "move_by": "any",
                        "within_plies": follow_window,
                    },
                ],
            }
        )

    return templates


def parse_prompt(text: str, mode: str | None = None, player: str | None = None, color: str | None = None) -> ParsedPrompt:
    text = normalize_space(text)
    parsed_mode = infer_mode(text, mode)
    parsed_player = infer_player(text, player)
    parsed_color = infer_color(text, color)
    filters = infer_filters(text)
    moves = extract_moves(text)
    square_facts = extract_square_facts(text)
    windows = extract_move_windows(text, len(moves))
    battery_hint = extract_battery_hint(text)
    defend_hint = extract_defend_hint(text)
    motif_templates = extract_motif_templates(text)
    sequence_templates = extract_sequence_templates(text)

    clarification_needed = None
    if not moves and not square_facts and not motif_templates and not sequence_templates:
        clarification_needed = "Need at least one anchor move or one concrete board fact (like 'knight on e5')."

    return ParsedPrompt(
        raw_text=text,
        mode=parsed_mode,
        player=parsed_player,
        color=parsed_color,
        filters=filters,
        moves=moves,
        square_facts=square_facts,
        move_windows=windows,
        battery_hint=battery_hint,
        defend_hint=defend_hint,
        motif_templates=motif_templates,
        sequence_templates=sequence_templates,
        clarification_needed=clarification_needed,
    )


def default_move_by(parsed: ParsedPrompt) -> str:
    return "self" if parsed.player else "any"


def choose_anchor_bishop_square(parsed: ParsedPrompt) -> str | None:
    for fact in parsed.square_facts:
        if fact["piece"] == "B":
            return fact["square"]
    return None


def effective_color_spec(spec: str, parsed: ParsedPrompt) -> str:
    if spec in {"self", "opponent"} and not parsed.player:
        return "any"
    return spec


def normalize_predicate_colors(pred: dict[str, Any], parsed: ParsedPrompt) -> dict[str, Any]:
    out = dict(pred)
    for key in ("color", "pinned_color", "attacker_color", "defender_color", "target_color"):
        if key in out:
            out[key] = effective_color_spec(out[key], parsed)
    return out


def normalize_move_template(step: dict[str, Any], parsed: ParsedPrompt) -> dict[str, Any]:
    out = dict(step)
    if "move_by" in out:
        out["move_by"] = effective_color_spec(out["move_by"], parsed)
    return out


def build_exact_query(parsed: ParsedPrompt, limit: int, context_window: int) -> dict[str, Any]:
    query: dict[str, Any] = {
        "limit": limit,
        "context_window": context_window,
        "sequence": [],
    }
    if parsed.player:
        query["player"] = parsed.player
    if parsed.color:
        query["color"] = parsed.color
    if parsed.filters:
        query["filters"] = parsed.filters

    move_by = default_move_by(parsed)

    if parsed.moves:
        for idx, move in enumerate(parsed.moves):
            step: dict[str, Any] = {
                "move": move,
                "move_by": move_by,
            }
            if idx < len(parsed.move_windows) and parsed.move_windows[idx] is not None:
                step["within_plies"] = parsed.move_windows[idx]
            if idx == 0 and parsed.square_facts:
                step["predicates"] = [
                    {
                        "type": "piece_on_square",
                        "phase": "before",
                        "color": effective_color_spec(fact["color"], parsed),
                        "piece": fact["piece"],
                        "square": fact["square"],
                    }
                    for fact in parsed.square_facts
                ]
            query["sequence"].append(step)
    else:
        predicates = [
            {
                "type": "piece_on_square",
                "phase": "before",
                "color": effective_color_spec(fact["color"], parsed),
                "piece": fact["piece"],
                "square": fact["square"],
            }
            for fact in parsed.square_facts
        ]
        if predicates:
            step = {
                "move_by": "any",
                "predicates": predicates,
            }
            query["sequence"].append(step)

    for motif in parsed.motif_templates:
        if not motif.get("required", True):
            continue
        if "predicate" in motif:
            if not query["sequence"]:
                query["sequence"].append({"move_by": "any", "predicates": []})
            pred = normalize_predicate_colors(motif["predicate"], parsed)
            query["sequence"][0].setdefault("predicates", []).append(pred)
        elif "move_template" in motif:
            query["sequence"].append(normalize_move_template(motif["move_template"], parsed))

    for template in parsed.sequence_templates:
        for step in template.get("steps", []):
            if "predicates" in step:
                query["sequence"].append(
                    {
                        **{k: v for k, v in step.items() if k != "predicates"},
                        "predicates": [normalize_predicate_colors(pred, parsed) for pred in step.get("predicates", [])],
                    }
                )
            else:
                query["sequence"].append(normalize_move_template(step, parsed))

    if parsed.battery_hint and parsed.player:
        query["sequence"][0].setdefault("predicates", []).append(
            {
                "type": "battery",
                "phase": "after" if parsed.moves else "before",
                "color": "self",
                "back_piece": "Q",
                "front_piece": "B",
            }
        )

    if parsed.defend_hint and parsed.player and parsed.moves and parsed.moves[0].startswith("Q"):
        bishop_square = choose_anchor_bishop_square(parsed)
        if bishop_square:
            query["sequence"][0].setdefault("predicates", []).append(
                {
                    "type": "move_adds_defender_to_piece",
                    "color": "self",
                    "defender_color": "self",
                    "defender_piece": "Q",
                    "piece": "B",
                    "square": bishop_square,
                }
            )

    return query


def build_fuzzy_query(parsed: ParsedPrompt, limit: int, context_window: int) -> dict[str, Any]:
    base = build_exact_query(parsed, limit=limit, context_window=context_window)
    sequence = base.pop("sequence")
    fuzzy = dict(base)
    fuzzy["sequence"] = []

    soften_motifs = bool(parsed.moves or parsed.square_facts)
    motif_predicates = [motif["predicate"] for motif in parsed.motif_templates if "predicate" in motif]

    for idx, step in enumerate(sequence):
        enriched = dict(step)
        if soften_motifs and idx == 0 and "predicates" in enriched:
            filtered_preds = []
            for pred in enriched["predicates"]:
                if parsed.battery_hint and pred.get("type") == "battery":
                    continue
                if parsed.defend_hint and pred.get("type") == "move_adds_defender_to_piece":
                    continue
                if pred in motif_predicates:
                    continue
                filtered_preds.append(pred)
            enriched["predicates"] = filtered_preds
        enriched["required"] = True
        fuzzy["sequence"].append(enriched)

    insert_at = 1 if parsed.moves else 0

    if soften_motifs:
        for motif in parsed.motif_templates:
            if "predicate" in motif:
                fuzzy["sequence"].insert(
                    insert_at,
                    {
                        "label": motif["label"],
                        "move_by": default_move_by(parsed) if parsed.moves else "any",
                        "within_plies": 0 if parsed.moves else 6,
                        "required": False,
                        "weight": 2.0,
                        "predicates": [normalize_predicate_colors(motif["predicate"], parsed)],
                    },
                )
            elif "move_template" in motif:
                step = normalize_move_template(motif["move_template"], parsed)
                step.update({
                    "label": motif["label"],
                    "within_plies": 6,
                    "required": False,
                    "weight": 2.0,
                })
                fuzzy["sequence"].insert(insert_at, step)
            insert_at += 1

    if parsed.battery_hint and parsed.player:
        fuzzy["sequence"].insert(
            insert_at,
            {
                "label": "battery motif",
                "move_by": default_move_by(parsed) if parsed.moves else "any",
                "within_plies": 0 if parsed.moves else 6,
                "required": False,
                "weight": 2.0,
                "predicates": [
                    {
                        "type": "battery",
                        "phase": "after" if parsed.moves else "before",
                        "color": "self",
                        "back_piece": "Q",
                        "front_piece": "B",
                    }
                ],
            },
        )

    if parsed.defend_hint and parsed.player and parsed.moves and parsed.moves[0].startswith("Q"):
        bishop_square = choose_anchor_bishop_square(parsed)
        if bishop_square:
            fuzzy["sequence"].insert(
                1,
                {
                    "label": f"queen adds defense to bishop on {bishop_square}",
                    "move": parsed.moves[0],
                    "move_by": default_move_by(parsed),
                    "required": False,
                    "weight": 3.0,
                    "predicates": [
                        {
                            "type": "move_adds_defender_to_piece",
                            "color": "self",
                            "defender_color": "self",
                            "defender_piece": "Q",
                            "piece": "B",
                            "square": bishop_square,
                        }
                    ],
                },
            )

    return fuzzy


def explain_parse(parsed: ParsedPrompt) -> dict[str, Any]:
    return {
        "raw_text": parsed.raw_text,
        "mode": parsed.mode,
        "player": parsed.player,
        "color": parsed.color,
        "filters": parsed.filters,
        "moves": parsed.moves,
        "square_facts": parsed.square_facts,
        "battery_hint": parsed.battery_hint,
        "defend_hint": parsed.defend_hint,
        "motif_templates": parsed.motif_templates,
        "sequence_templates": parsed.sequence_templates,
        "clarification_needed": parsed.clarification_needed,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Natural-language wrapper for chess-db structured query search")
    p.add_argument("text", nargs="*", help="Natural-language chess query")
    p.add_argument("--db", default=DB_PATH, help="Path to PGN database")
    p.add_argument("--mode", choices=["auto", "exact", "fuzzy"], default="auto")
    p.add_argument("--player", help="Force player name")
    p.add_argument("--color", choices=["white", "black"], help="Force color")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--context-window", type=int, default=2)
    p.add_argument("--parse-only", action="store_true", help="Only show how the prompt was parsed")
    p.add_argument("--compile-only", action="store_true", help="Only show compiled JSON query")
    p.add_argument("--pretty", action="store_true", help="Show a human summary before JSON")
    return p


def pretty_results(payload: dict[str, Any]) -> None:
    results = payload.get("results", [])
    print(f"{payload.get('returned', 0)} result(s) from {payload.get('scanned_games', 0)} scanned game(s) [{payload.get('mode', 'exact')}]\n")
    for idx, item in enumerate(results, 1):
        print(f"{idx}. {item.get('white', '?')} vs {item.get('black', '?')} ({item.get('result', '*')})")
        if item.get("study"):
            print(f"   Study: {item['study']}")
        if item.get("chapter"):
            print(f"   Chapter: {item['chapter']}")
        if item.get("url"):
            print(f"   URL: {item['url']}")
        if item.get("score") is not None:
            print(f"   Score: {item['score']:.2f}")
        print("   Matched sequence:")
        for move in item.get("matched_moves", []):
            dot = "." if move["turn"] == "white" else "..."
            print(f"     {move['move_number']}{dot} {move['san']} (ply {move['ply']})")
        if item.get("matched_optional"):
            print("   Optional hits:")
            for opt in item["matched_optional"]:
                print(f"     + {opt['label']} (weight {opt['weight']})")
        if item.get("missed_optional"):
            print("   Optional misses:")
            for opt in item["missed_optional"]:
                print(f"     - {opt['label']} (weight {opt['weight']})")
        print()


def main() -> int:
    args = build_parser().parse_args()
    text = normalize_space(" ".join(args.text))
    if not text:
        print("Need a natural-language query.", file=sys.stderr)
        return 2

    forced_mode = None if args.mode == "auto" else args.mode
    parsed = parse_prompt(text, mode=forced_mode, player=args.player, color=args.color)

    if args.parse_only:
        print(json.dumps(explain_parse(parsed), indent=2, ensure_ascii=False))
        return 0

    if parsed.clarification_needed:
        payload = {
            "status": "needs_clarification",
            "parse": explain_parse(parsed),
            "message": parsed.clarification_needed,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    compiled = build_fuzzy_query(parsed, args.limit, args.context_window) if parsed.mode == "fuzzy" else build_exact_query(parsed, args.limit, args.context_window)

    if args.compile_only:
        payload = {
            "mode": parsed.mode,
            "parse": explain_parse(parsed),
            "compiled_query": compiled,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    try:
        if parsed.mode == "fuzzy":
            payload = run_fuzzy_query(compiled, path=args.db)
        else:
            payload = run_query(compiled, path=args.db)
            payload["mode"] = "exact"
        payload["parse"] = explain_parse(parsed)
        payload["compiled_query"] = compiled
    except QueryError as e:
        print(f"Query error: {e}", file=sys.stderr)
        return 2

    if args.pretty:
        pretty_results(payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
