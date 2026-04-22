#!/usr/bin/env python3
"""Fuzzy query compiler/runner for chess-db.

Purpose:
- give the model a softer JSON target for positional idea search
- compile required constraints into deterministic search behavior
- rank results by optional motif matches instead of forcing everything to be exact
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from query_engine import (
    DB_PATH,
    Candidate,
    MoveContext,
    QueryError,
    candidate_to_dict,
    collapse_motif_candidates,
    game_focus_color,
    headers_match,
    iter_game_contexts,
    move_matches,
)


@dataclass
class FuzzyMatch:
    candidate: Candidate
    score: float
    matched_optional: list[dict[str, Any]]
    missed_optional: list[dict[str, Any]]


META_STEP_FIELDS = {"required", "weight", "label", "description"}


def _normalize_sequence(fuzzy_query: dict[str, Any]) -> list[dict[str, Any]]:
    if "sequence" not in fuzzy_query or not fuzzy_query["sequence"]:
        raise QueryError("Fuzzy query requires a non-empty 'sequence'")
    seq = []
    for idx, step in enumerate(fuzzy_query["sequence"]):
        if not isinstance(step, dict):
            raise QueryError(f"Fuzzy sequence step {idx} must be an object")
        norm = dict(step)
        norm.setdefault("required", idx == 0)
        norm.setdefault("weight", 1.0)
        seq.append(norm)
    return seq


def _strip_step_meta(step: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in step.items() if k not in META_STEP_FIELDS}


def compile_fuzzy_to_exact(fuzzy_query: dict[str, Any]) -> dict[str, Any]:
    seq = _normalize_sequence(fuzzy_query)
    exact_sequence = [_strip_step_meta(step) for step in seq if step.get("required", False)]
    if not exact_sequence:
        raise QueryError("Fuzzy query must contain at least one required step")

    exact = {
        key: fuzzy_query[key]
        for key in ("player", "color", "filters", "limit", "context_window")
        if key in fuzzy_query
    }
    exact["sequence"] = exact_sequence
    return exact


def _step_label(step: dict[str, Any], index: int) -> str:
    if step.get("label"):
        return str(step["label"])
    if step.get("move"):
        return f"step {index + 1}: {step['move']}"
    if step.get("uci"):
        return f"step {index + 1}: {step['uci']}"
    return f"step {index + 1}"


def _make_candidate(first: MoveContext, picked: list[MoveContext], focus_color, reasons: list[str]) -> Candidate:
    return Candidate(
        game_id=first.game_id,
        headers=first.headers,
        study=first.study,
        chapter=first.chapter,
        url=first.url,
        focus_color=focus_color,
        moves=picked,
        reasons=reasons,
    )


def _search_game_fuzzy(
    contexts: list[MoveContext],
    sequence: list[dict[str, Any]],
    focus_color,
) -> list[FuzzyMatch]:
    matches: list[FuzzyMatch] = []

    def rec(
        step_idx: int,
        start_pos: int,
        picked: list[MoveContext],
        reasons: list[str],
        score: float,
        matched_optional: list[dict[str, Any]],
        missed_optional: list[dict[str, Any]],
    ):
        if step_idx >= len(sequence):
            if not picked:
                return
            first = picked[0]
            matches.append(
                FuzzyMatch(
                    candidate=_make_candidate(first, picked, focus_color, reasons),
                    score=score,
                    matched_optional=matched_optional,
                    missed_optional=missed_optional,
                )
            )
            return

        step = sequence[step_idx]
        executable = _strip_step_meta(step)
        required = bool(step.get("required", False))
        weight = float(step.get("weight", 1.0))
        last_ply = picked[-1].ply if picked else None
        within = executable.get("within_plies")
        found = False

        for pos in range(start_pos, len(contexts)):
            ctx = contexts[pos]
            if last_ply is not None and within is not None and ctx.ply - last_ply > within:
                break
            ok, why = move_matches(executable, ctx, focus_color)
            if not ok:
                continue
            found = True
            next_score = score + (weight if not required else 0.0)
            next_matched_optional = list(matched_optional)
            if not required:
                next_matched_optional.append(
                    {
                        "step_index": step_idx,
                        "label": _step_label(step, step_idx),
                        "weight": weight,
                        "ply": ctx.ply,
                        "san": ctx.san,
                    }
                )
            rec(
                step_idx + 1,
                pos + 1,
                picked + [ctx],
                reasons + why,
                next_score,
                next_matched_optional,
                list(missed_optional),
            )

        if not found and not required:
            next_missed = list(missed_optional)
            next_missed.append(
                {
                    "step_index": step_idx,
                    "label": _step_label(step, step_idx),
                    "weight": weight,
                }
            )
            rec(step_idx + 1, start_pos, picked, reasons, score, list(matched_optional), next_missed)

    rec(0, 0, [], [], 0.0, [], [])
    return matches


def run_fuzzy_query(fuzzy_query: dict[str, Any], path: str = DB_PATH) -> dict[str, Any]:
    sequence = _normalize_sequence(fuzzy_query)
    limit = int(fuzzy_query.get("limit", 10))
    window = int(fuzzy_query.get("context_window", 3))

    scanned_games = 0
    results: list[dict[str, Any]] = []
    raw_matches: list[FuzzyMatch] = []
    context_cache: dict[int, list[MoveContext]] = {}

    for game_id, headers, contexts in iter_game_contexts(path):
        scanned_games += 1
        context_cache[game_id] = contexts
        if not headers_match(headers, fuzzy_query):
            continue
        focus_color = game_focus_color(headers, fuzzy_query)
        if fuzzy_query.get("player") and focus_color is None:
            continue
        if fuzzy_query.get("color") in ("white", "black") and focus_color is None:
            continue
        raw_matches.extend(_search_game_fuzzy(contexts, sequence, focus_color))

    motif_only = len(sequence) == 1 and not _strip_step_meta(sequence[0]).get("move") and not _strip_step_meta(sequence[0]).get("uci")
    if motif_only:
        grouped: list[FuzzyMatch] = []
        by_score: dict[tuple[int, tuple[str, ...], float], list[FuzzyMatch]] = {}
        for match in raw_matches:
            key = (match.candidate.game_id, tuple(match.candidate.reasons), match.score)
            by_score.setdefault(key, []).append(match)
        for group in by_score.values():
            collapsed = collapse_motif_candidates([m.candidate for m in group])
            for cand in collapsed:
                template = group[0]
                grouped.append(
                    FuzzyMatch(
                        candidate=cand,
                        score=template.score,
                        matched_optional=template.matched_optional,
                        missed_optional=template.missed_optional,
                    )
                )
        raw_matches = grouped

    raw_matches.sort(
        key=lambda m: (
            -m.score,
            -len(m.matched_optional),
            m.candidate.moves[0].game_id,
            m.candidate.moves[0].ply,
        )
    )

    for match in raw_matches[:limit]:
        item = candidate_to_dict(match.candidate, context_cache.get(match.candidate.game_id, []), window=window)
        item["score"] = match.score
        item["matched_optional"] = match.matched_optional
        item["missed_optional"] = match.missed_optional
        results.append(item)

    return {
        "mode": "fuzzy",
        "fuzzy_query": fuzzy_query,
        "compiled_exact_query": compile_fuzzy_to_exact(fuzzy_query),
        "db_path": path,
        "scanned_games": scanned_games,
        "returned": len(results),
        "results": results,
    }
