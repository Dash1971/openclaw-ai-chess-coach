#!/usr/bin/env python3
"""General position/motif query engine for chess-db.

Purpose:
- do deterministic retrieval over PGN data
- let the LLM translate natural-language chess questions into structured queries
- keep models out of the business of searching raw PGN text

This is intentionally query-first, not opening-prefix-only and not regex-based.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Iterable

import chess
import chess.pgn

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "games.pgn")

RESULTS_DEFAULT = 10
WINDOW_DEFAULT = 3

PIECE_TYPES = {
    "P": chess.PAWN,
    "N": chess.KNIGHT,
    "B": chess.BISHOP,
    "R": chess.ROOK,
    "Q": chess.QUEEN,
    "K": chess.KING,
}

COLOR_NAMES = {
    chess.WHITE: "white",
    chess.BLACK: "black",
}


@dataclass
class MoveContext:
    game_id: int
    headers: dict[str, str]
    study: str
    chapter: str
    url: str
    ply: int
    move_number: int
    turn: chess.Color
    san: str
    uci: str
    before_fen: str
    after_fen: str
    before: chess.Board
    after: chess.Board


@dataclass
class Candidate:
    game_id: int
    headers: dict[str, str]
    study: str
    chapter: str
    url: str
    focus_color: chess.Color | None
    moves: list[MoveContext]
    reasons: list[str]
    occurrence_count: int = 1
    occurrence_start_ply: int | None = None
    occurrence_end_ply: int | None = None


class QueryError(ValueError):
    pass


def square_name_to_index(name: str) -> chess.Square:
    try:
        return chess.parse_square(name)
    except ValueError as e:
        raise QueryError(f"Invalid square: {name}") from e


def piece_symbol_to_type(symbol: str) -> int:
    symbol = symbol.upper()
    if symbol not in PIECE_TYPES:
        raise QueryError(f"Invalid piece symbol: {symbol}")
    return PIECE_TYPES[symbol]


def normalize_text(value: str) -> str:
    return value.lower().strip()


def headers_match(headers: dict[str, str], query: dict[str, Any]) -> bool:
    filters = query.get("filters", {})
    for key, header_name in (
        ("study_contains", "StudyName"),
        ("chapter_contains", "ChapterName"),
        ("event_contains", "Event"),
        ("opening_contains", "Opening"),
        ("site_contains", "Site"),
    ):
        wanted = filters.get(key)
        if wanted and normalize_text(wanted) not in normalize_text(headers.get(header_name, "")):
            return False
    return True


def game_focus_color(headers: dict[str, str], query: dict[str, Any]) -> chess.Color | None:
    player = query.get("player")
    color = query.get("color", "any")

    if color not in ("white", "black", "any"):
        raise QueryError("query.color must be 'white', 'black', or 'any'")

    if not player:
        if color == "white":
            return chess.WHITE
        if color == "black":
            return chess.BLACK
        return None

    player = normalize_text(player)
    white = normalize_text(headers.get("White", ""))
    black = normalize_text(headers.get("Black", ""))

    matches_white = player in white
    matches_black = player in black

    if color == "white":
        return chess.WHITE if matches_white else None
    if color == "black":
        return chess.BLACK if matches_black else None

    if matches_white and not matches_black:
        return chess.WHITE
    if matches_black and not matches_white:
        return chess.BLACK
    if matches_white and matches_black:
        return None
    return None


def iter_game_contexts(path: str = DB_PATH) -> Iterable[tuple[int, dict[str, str], list[MoveContext]]]:
    with open(path, encoding="utf-8", errors="ignore") as f:
        game_id = 0
        while True:
            with contextlib.redirect_stderr(io.StringIO()):
                game = chess.pgn.read_game(f)
            if game is None:
                break
            game_id += 1
            board = game.board()
            contexts: list[MoveContext] = []
            ply = 0
            malformed = False
            for move in game.mainline_moves():
                before = board.copy(stack=False)
                try:
                    san = board.san(move)
                    board.push(move)
                except Exception:
                    malformed = True
                    break
                after = board.copy(stack=False)
                ply += 1
                contexts.append(
                    MoveContext(
                        game_id=game_id,
                        headers=dict(game.headers),
                        study=game.headers.get("StudyName", "Unknown Study"),
                        chapter=game.headers.get("ChapterName", ""),
                        url=game.headers.get("ChapterURL", ""),
                        ply=ply,
                        move_number=before.fullmove_number,
                        turn=before.turn,
                        san=san,
                        uci=move.uci(),
                        before_fen=before.fen(),
                        after_fen=after.fen(),
                        before=before,
                        after=after,
                    )
                )
            if malformed or not contexts:
                continue
            yield game_id, dict(game.headers), contexts


def resolve_color(spec: str | None, focus_color: chess.Color | None) -> chess.Color | None:
    if spec is None or spec == "any":
        return None
    if spec == "white":
        return chess.WHITE
    if spec == "black":
        return chess.BLACK
    if spec == "self":
        if focus_color is None:
            raise QueryError("Predicate uses color='self' but query has no focus color")
        return focus_color
    if spec == "opponent":
        if focus_color is None:
            raise QueryError("Predicate uses color='opponent' but query has no focus color")
        return not focus_color
    raise QueryError(f"Unsupported color spec: {spec}")


def resolve_turn(spec: str | None, focus_color: chess.Color | None) -> chess.Color | None:
    return resolve_color(spec, focus_color)


def get_piece(board: chess.Board, square: str) -> chess.Piece | None:
    return board.piece_at(square_name_to_index(square))


def piece_matches(piece: chess.Piece | None, piece_symbol: str | None, color: chess.Color | None) -> bool:
    if piece is None:
        return False
    if piece_symbol and piece.piece_type != piece_symbol_to_type(piece_symbol):
        return False
    if color is not None and piece.color != color:
        return False
    return True


def attackers_of_type(board: chess.Board, target_sq: chess.Square, color: chess.Color, piece_symbol: str | None = None) -> list[chess.Square]:
    out = []
    for sq in board.attackers(color, target_sq):
        piece = board.piece_at(sq)
        if piece_matches(piece, piece_symbol, color):
            out.append(sq)
    return out


def same_line(square_a: chess.Square, square_b: chess.Square) -> bool:
    file_a = chess.square_file(square_a)
    rank_a = chess.square_rank(square_a)
    file_b = chess.square_file(square_b)
    rank_b = chess.square_rank(square_b)
    return (
        file_a == file_b
        or rank_a == rank_b
        or abs(file_a - file_b) == abs(rank_a - rank_b)
    )


def pieces_of(board: chess.Board, color: chess.Color, piece_symbol: str) -> list[chess.Square]:
    piece_type = piece_symbol_to_type(piece_symbol)
    return list(board.pieces(piece_type, color))


def file_name_to_index(name: str) -> int:
    if len(name) != 1 or name not in "abcdefgh":
        raise QueryError(f"Invalid file: {name}")
    return ord(name) - ord("a")


def open_file(board: chess.Board, file_idx: int) -> bool:
    for rank in range(8):
        sq = chess.square(file_idx, rank)
        piece = board.piece_at(sq)
        if piece and piece.piece_type == chess.PAWN:
            return False
    return True


def semi_open_file(board: chess.Board, file_idx: int, color: chess.Color) -> bool:
    own_pawn = False
    opp_pawn = False
    for rank in range(8):
        sq = chess.square(file_idx, rank)
        piece = board.piece_at(sq)
        if piece and piece.piece_type == chess.PAWN:
            if piece.color == color:
                own_pawn = True
            else:
                opp_pawn = True
    return (not own_pawn) and opp_pawn


def castled_side(board: chess.Board, color: chess.Color) -> str | None:
    king_sq = board.king(color)
    if king_sq is None:
        return None
    file_idx = chess.square_file(king_sq)
    if file_idx >= 6:
        return "king"
    if file_idx <= 2:
        return "queen"
    return None


def pawn_advanced_enough(square: chess.Square, color: chess.Color, min_advance: int) -> bool:
    rank = chess.square_rank(square)
    start_rank = 1 if color == chess.WHITE else 6
    advance = rank - start_rank if color == chess.WHITE else start_rank - rank
    return advance >= min_advance


def piece_advanced_enough(square: chess.Square, color: chess.Color, min_advance: int, start_rank: int | None = None) -> bool:
    rank = chess.square_rank(square)
    if start_rank is None:
        start_rank = 0 if color == chess.WHITE else 7
    advance = rank - start_rank if color == chess.WHITE else start_rank - rank
    return advance >= min_advance


def square_has_pawn_defender(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    return bool(attackers_of_type(board, square, color, "P"))


def square_attacked_by_opponent_pawn(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    return bool(attackers_of_type(board, square, not color, "P"))


def piece_pins_to_target(board: chess.Board, pinned_sq: chess.Square, attacker_color: chess.Color, target_piece_symbol: str) -> tuple[bool, str | None]:
    pinned_piece = board.piece_at(pinned_sq)
    if pinned_piece is None:
        return False, None
    target_color = pinned_piece.color

    if target_piece_symbol == "K":
        ok = board.is_pinned(target_color, pinned_sq)
        if not ok:
            return False, None
        king_sq = board.king(target_color)
        if king_sq is None:
            return False, None
        return True, chess.square_name(king_sq)

    if target_piece_symbol != "Q":
        raise QueryError("pin target_piece must be 'K' or 'Q'")

    queens = pieces_of(board, target_color, "Q")
    sliders = {chess.BISHOP, chess.ROOK, chess.QUEEN}
    for target_sq in queens:
        if not same_line(pinned_sq, target_sq):
            continue
        if any(board.piece_at(sq) for sq in chess.between(pinned_sq, target_sq)):
            continue
        direction_file = (chess.square_file(pinned_sq) - chess.square_file(target_sq))
        direction_rank = (chess.square_rank(pinned_sq) - chess.square_rank(target_sq))
        step_file = 0 if direction_file == 0 else (1 if direction_file > 0 else -1)
        step_rank = 0 if direction_rank == 0 else (1 if direction_rank > 0 else -1)
        cur_file = chess.square_file(pinned_sq) + step_file
        cur_rank = chess.square_rank(pinned_sq) + step_rank
        while 0 <= cur_file < 8 and 0 <= cur_rank < 8:
            sq = chess.square(cur_file, cur_rank)
            piece = board.piece_at(sq)
            if piece is None:
                cur_file += step_file
                cur_rank += step_rank
                continue
            if piece.color != attacker_color or piece.piece_type not in sliders:
                break
            aligned_diagonal = abs(step_file) == abs(step_rank) and piece.piece_type in {chess.BISHOP, chess.QUEEN}
            aligned_straight = (step_file == 0 or step_rank == 0) and piece.piece_type in {chess.ROOK, chess.QUEEN}
            if aligned_diagonal or aligned_straight:
                return True, chess.square_name(target_sq)
            break
    return False, None


def predicate_ok(pred: dict[str, Any], ctx: MoveContext, focus_color: chess.Color | None) -> tuple[bool, str | None]:
    kind = pred.get("type")
    phase = pred.get("phase", "before")
    board = ctx.before if phase == "before" else ctx.after

    if kind == "piece_on_square":
        square = pred["square"]
        color = resolve_color(pred.get("color", "any"), focus_color)
        piece = get_piece(board, square)
        ok = piece_matches(piece, pred.get("piece"), color)
        if ok:
            p = piece.symbol().upper() if piece else "?"
            return True, f"{phase}: {COLOR_NAMES[piece.color]} {p} on {square}"
        return False, None

    if kind == "piece_count":
        color = resolve_color(pred.get("color", "any"), focus_color)
        piece_symbol = pred.get("piece")
        if not piece_symbol:
            raise QueryError("piece_count requires 'piece'")
        if color is None:
            count = len(board.pieces(piece_symbol_to_type(piece_symbol), chess.WHITE)) + len(board.pieces(piece_symbol_to_type(piece_symbol), chess.BLACK))
        else:
            count = len(board.pieces(piece_symbol_to_type(piece_symbol), color))
        min_count = pred.get("min", 0)
        max_count = pred.get("max")
        ok = count >= min_count and (max_count is None or count <= max_count)
        return (True, f"{phase}: {count} {piece_symbol.upper()} pieces") if ok else (False, None)

    if kind == "move_adds_defender_to_square":
        square = square_name_to_index(pred["square"])
        color = resolve_color(pred.get("color", "self"), focus_color)
        piece_symbol = pred.get("piece")
        before_count = len(attackers_of_type(ctx.before, square, color, piece_symbol))
        after_count = len(attackers_of_type(ctx.after, square, color, piece_symbol))
        ok = after_count > before_count
        if ok:
            return True, f"move adds defender(s) to {pred['square']} ({before_count}→{after_count})"
        return False, None

    if kind == "piece_defended":
        square = pred["square"]
        piece_symbol = pred.get("piece")
        defended_color = resolve_color(pred.get("color", "self"), focus_color)
        defender_color = resolve_color(pred.get("defender_color", pred.get("color", "self")), focus_color)
        defender_piece = pred.get("defender_piece")
        target_piece = get_piece(board, square)
        if not piece_matches(target_piece, piece_symbol, defended_color):
            return False, None
        attacker_squares = attackers_of_type(board, square_name_to_index(square), defender_color, defender_piece)
        if attacker_squares:
            ds = ",".join(chess.square_name(sq) for sq in attacker_squares)
            return True, f"{phase}: {square} defended by {defender_piece or 'piece'} from {ds}"
        return False, None

    if kind == "move_adds_defender_to_piece":
        square = pred["square"]
        target_piece = pred.get("piece")
        defended_color = resolve_color(pred.get("color", "self"), focus_color)
        defender_color = resolve_color(pred.get("defender_color", pred.get("color", "self")), focus_color)
        defender_piece = pred.get("defender_piece")
        before_piece = get_piece(ctx.before, square)
        after_piece = get_piece(ctx.after, square)
        if not piece_matches(before_piece, target_piece, defended_color):
            return False, None
        if not piece_matches(after_piece, target_piece, defended_color):
            return False, None
        target_sq = square_name_to_index(square)
        before_count = len(attackers_of_type(ctx.before, target_sq, defender_color, defender_piece))
        after_count = len(attackers_of_type(ctx.after, target_sq, defender_color, defender_piece))
        ok = after_count > before_count
        if ok:
            return True, f"move adds defense to {square} ({before_count}→{after_count})"
        return False, None

    if kind == "battery":
        color = resolve_color(pred.get("color", "self"), focus_color)
        back_piece = pred.get("back_piece", "Q")
        front_piece = pred.get("front_piece", "B")
        board_to_check = board
        colors = [color] if color is not None else [chess.WHITE, chess.BLACK]
        for side in colors:
            back_sqs = pieces_of(board_to_check, side, back_piece)
            front_sqs = pieces_of(board_to_check, side, front_piece)
            for back_sq in back_sqs:
                for front_sq in front_sqs:
                    if back_sq == front_sq:
                        continue
                    if same_line(back_sq, front_sq):
                        return True, f"{phase}: {COLOR_NAMES[side]} {back_piece}@{chess.square_name(back_sq)} behind {front_piece}@{chess.square_name(front_sq)}"
        return False, None

    if kind == "piece_attacks_square":
        target_sq = square_name_to_index(pred["target_square"])
        piece_symbol = pred.get("piece")
        if not piece_symbol:
            raise QueryError("piece_attacks_square requires 'piece'")
        color = resolve_color(pred.get("color", "any"), focus_color)
        from_square = pred.get("from_square")
        if from_square:
            from_sq = square_name_to_index(from_square)
            piece = board.piece_at(from_sq)
            ok = piece_matches(piece, piece_symbol, color) and target_sq in board.attacks(from_sq)
            if ok:
                return True, f"{phase}: {piece_symbol}@{from_square} attacks {pred['target_square']}"
            return False, None
        colors = [color] if color is not None else [chess.WHITE, chess.BLACK]
        for side in colors:
            for from_sq in pieces_of(board, side, piece_symbol):
                if target_sq in board.attacks(from_sq):
                    return True, f"{phase}: {COLOR_NAMES[side]} {piece_symbol}@{chess.square_name(from_sq)} attacks {pred['target_square']}"
        return False, None

    if kind == "rook_on_open_file":
        color = resolve_color(pred.get("color", "any"), focus_color)
        file_idx = file_name_to_index(pred["file"]) if pred.get("file") else chess.square_file(square_name_to_index(pred["square"]))
        if not open_file(board, file_idx):
            return False, None
        colors = [color] if color is not None else [chess.WHITE, chess.BLACK]
        for side in colors:
            rooks = [sq for sq in pieces_of(board, side, "R") if chess.square_file(sq) == file_idx]
            if rooks:
                squares = ",".join(chess.square_name(sq) for sq in rooks)
                return True, f"{phase}: {COLOR_NAMES[side]} rook on open {chr(file_idx + ord('a'))}-file from {squares}"
        return False, None

    if kind == "rook_on_semi_open_file":
        color = resolve_color(pred.get("color", "any"), focus_color)
        file_idx = file_name_to_index(pred["file"]) if pred.get("file") else chess.square_file(square_name_to_index(pred["square"]))
        colors = [color] if color is not None else [chess.WHITE, chess.BLACK]
        for side in colors:
            if not semi_open_file(board, file_idx, side):
                continue
            rooks = [sq for sq in pieces_of(board, side, "R") if chess.square_file(sq) == file_idx]
            if rooks:
                squares = ",".join(chess.square_name(sq) for sq in rooks)
                return True, f"{phase}: {COLOR_NAMES[side]} rook on semi-open {chr(file_idx + ord('a'))}-file from {squares}"
        return False, None

    if kind == "battery_toward_square":
        color = resolve_color(pred.get("color", "self"), focus_color)
        back_piece = pred.get("back_piece", "Q")
        front_piece = pred.get("front_piece", "B")
        target_sq = square_name_to_index(pred["target_square"])
        colors = [color] if color is not None else [chess.WHITE, chess.BLACK]
        for side in colors:
            for back_sq in pieces_of(board, side, back_piece):
                for front_sq in pieces_of(board, side, front_piece):
                    if back_sq == front_sq or not same_line(back_sq, front_sq):
                        continue
                    if target_sq not in board.attacks(front_sq):
                        continue
                    return True, f"{phase}: {COLOR_NAMES[side]} {back_piece}@{chess.square_name(back_sq)} behind {front_piece}@{chess.square_name(front_sq)} toward {pred['target_square']}"
        return False, None

    if kind == "opposite_side_castling":
        white_side = castled_side(board, chess.WHITE)
        black_side = castled_side(board, chess.BLACK)
        if white_side and black_side and white_side != black_side:
            return True, f"{phase}: opposite-side castling (white {white_side}side, black {black_side}side)"
        return False, None

    if kind == "pawn_storm_against_castled_king":
        attacker_color = resolve_color(pred.get("color", "any"), focus_color)
        target_color = resolve_color(pred.get("target_color", "any"), focus_color)
        target_side = pred.get("target_side")
        min_count = int(pred.get("min_count", 2))
        min_advance = int(pred.get("min_advance", 2))

        attacker_colors = [attacker_color] if attacker_color is not None else [chess.WHITE, chess.BLACK]
        for side in attacker_colors:
            inferred_target = target_color if target_color is not None else (not side)
            castled = castled_side(board, inferred_target)
            if castled is None:
                continue
            if target_side and castled != target_side:
                continue
            files = [5, 6, 7] if castled == "king" else [0, 1, 2]
            pawns = [sq for sq in pieces_of(board, side, "P") if chess.square_file(sq) in files and pawn_advanced_enough(sq, side, min_advance)]
            if len(pawns) >= min_count:
                pawn_squares = ",".join(chess.square_name(sq) for sq in pawns)
                return True, f"{phase}: {COLOR_NAMES[side]} pawn storm toward {COLOR_NAMES[inferred_target]} {castled}side king from {pawn_squares}"
        return False, None

    if kind == "rook_lifted":
        color = resolve_color(pred.get("color", "any"), focus_color)
        min_advance = int(pred.get("min_advance", 2))
        target_file = pred.get("file")
        colors = [color] if color is not None else [chess.WHITE, chess.BLACK]
        for side in colors:
            rooks = []
            for sq in pieces_of(board, side, "R"):
                if not piece_advanced_enough(sq, side, min_advance):
                    continue
                if target_file and chess.square_file(sq) != file_name_to_index(target_file):
                    continue
                rooks.append(sq)
            if rooks:
                squares = ",".join(chess.square_name(sq) for sq in rooks)
                return True, f"{phase}: {COLOR_NAMES[side]} lifted rook from {squares}"
        return False, None

    if kind == "piece_pinned_to_target":
        pinned_sq = square_name_to_index(pred["square"])
        attacker_color = resolve_color(pred.get("attacker_color", "opponent"), focus_color)
        pinned_color = resolve_color(pred.get("pinned_color", "self"), focus_color)
        piece = board.piece_at(pinned_sq)
        if piece is None:
            return False, None
        if pinned_color is not None and piece.color != pinned_color:
            return False, None
        if pred.get("piece") and piece.piece_type != piece_symbol_to_type(pred["piece"]):
            return False, None
        ok, target_square = piece_pins_to_target(board, pinned_sq, attacker_color, pred.get("target_piece", "K"))
        if ok:
            return True, f"{phase}: {COLOR_NAMES[piece.color]} {piece.symbol().upper()} on {pred['square']} pinned to {pred.get('target_piece', 'K')} on {target_square}"
        return False, None

    if kind == "knight_outpost":
        square = pred["square"]
        sq = square_name_to_index(square)
        piece = board.piece_at(sq)
        wanted_color = resolve_color(pred.get("color", "any"), focus_color)
        if piece is None or piece.piece_type != chess.KNIGHT:
            return False, None
        if wanted_color is not None and piece.color != wanted_color:
            return False, None
        if not square_has_pawn_defender(board, sq, piece.color):
            return False, None
        if square_attacked_by_opponent_pawn(board, sq, piece.color):
            return False, None
        return True, f"{phase}: {COLOR_NAMES[piece.color]} knight outpost on {square}"

    if kind == "san_contains":
        wanted = pred.get("text", "")
        target = ctx.san if phase == "after" else ctx.san
        ok = wanted in target
        return (True, f"SAN contains {wanted}") if ok else (False, None)

    raise QueryError(f"Unsupported predicate type: {kind}")


def move_matches(step: dict[str, Any], ctx: MoveContext, focus_color: chess.Color | None) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    move_by = resolve_turn(step.get("move_by", "any"), focus_color)
    if move_by is not None and ctx.turn != move_by:
        return False, []

    san = step.get("move")
    if san:
        if step.get("move_mode", "exact") == "regex":
            if not re.fullmatch(san, ctx.san):
                return False, []
        else:
            if ctx.san != san:
                return False, []
        reasons.append(f"move {ctx.san} at ply {ctx.ply}")

    uci = step.get("uci")
    if uci and ctx.uci != uci:
        return False, []
    if uci:
        reasons.append(f"uci {ctx.uci}")

    for pred in step.get("predicates", []):
        ok, why = predicate_ok(pred, ctx, focus_color)
        if not ok:
            return False, []
        if why:
            reasons.append(why)

    return True, reasons


def sequence_matches(contexts: list[MoveContext], sequence: list[dict[str, Any]], focus_color: chess.Color | None) -> list[Candidate]:
    matches: list[Candidate] = []
    if not sequence:
        return matches

    def rec(step_idx: int, start_pos: int, picked: list[MoveContext], reasons: list[str]):
        step = sequence[step_idx]
        last_ply = picked[-1].ply if picked else None
        within = step.get("within_plies")

        for pos in range(start_pos, len(contexts)):
            ctx = contexts[pos]
            if last_ply is not None and within is not None and ctx.ply - last_ply > within:
                break
            ok, why = move_matches(step, ctx, focus_color)
            if not ok:
                continue
            next_picked = picked + [ctx]
            next_reasons = reasons + why
            if step_idx == len(sequence) - 1:
                first = next_picked[0]
                matches.append(
                    Candidate(
                        game_id=first.game_id,
                        headers=first.headers,
                        study=first.study,
                        chapter=first.chapter,
                        url=first.url,
                        focus_color=focus_color,
                        moves=next_picked,
                        reasons=next_reasons,
                    )
                )
            else:
                rec(step_idx + 1, pos + 1, next_picked, next_reasons)

    rec(0, 0, [], [])
    return matches


def candidate_to_dict(c: Candidate, contexts: list[MoveContext], window: int = WINDOW_DEFAULT) -> dict[str, Any]:
    first_ply = c.moves[0].ply
    last_ply = c.moves[-1].ply
    occurrence_start = c.occurrence_start_ply or first_ply
    occurrence_end = c.occurrence_end_ply or last_ply
    excerpt = [ctx for ctx in contexts if first_ply - window <= ctx.ply <= last_ply + window]
    return {
        "game_id": c.game_id,
        "white": c.headers.get("White", "?"),
        "black": c.headers.get("Black", "?"),
        "result": c.headers.get("Result", "*"),
        "study": c.study,
        "chapter": c.chapter,
        "url": c.url,
        "focus_color": COLOR_NAMES.get(c.focus_color) if c.focus_color is not None else None,
        "matched_moves": [
            {
                "ply": m.ply,
                "move_number": m.move_number,
                "turn": COLOR_NAMES[m.turn],
                "san": m.san,
                "uci": m.uci,
                "before_fen": m.before_fen,
                "after_fen": m.after_fen,
            }
            for m in c.moves
        ],
        "context_window": [
            {
                "ply": m.ply,
                "move_number": m.move_number,
                "turn": COLOR_NAMES[m.turn],
                "san": m.san,
            }
            for m in excerpt
        ],
        "reasons": c.reasons,
        "occurrence_count": c.occurrence_count,
        "occurrence_start_ply": occurrence_start,
        "occurrence_end_ply": occurrence_end,
    }


def collapse_motif_candidates(candidates: list[Candidate], gap_plies: int = 2) -> list[Candidate]:
    if not candidates:
        return []
    ordered = sorted(candidates, key=lambda c: (c.game_id, c.moves[0].ply))
    collapsed: list[Candidate] = []
    current = ordered[0]
    current.occurrence_start_ply = current.moves[0].ply
    current.occurrence_end_ply = current.moves[-1].ply
    current.occurrence_count = 1

    for cand in ordered[1:]:
        cand_start = cand.moves[0].ply
        cand_end = cand.moves[-1].ply
        same_game = cand.game_id == current.game_id
        close = cand_start - (current.occurrence_end_ply or current.moves[-1].ply) <= gap_plies
        same_reason_shape = cand.reasons == current.reasons
        if same_game and close and same_reason_shape:
            current.occurrence_end_ply = cand_end
            current.occurrence_count += 1
            continue
        collapsed.append(current)
        current = cand
        current.occurrence_start_ply = cand_start
        current.occurrence_end_ply = cand_end
        current.occurrence_count = 1

    collapsed.append(current)
    return collapsed


def run_query(query: dict[str, Any], path: str = DB_PATH) -> dict[str, Any]:
    sequence = query.get("sequence", [])
    if not sequence:
        raise QueryError("Query requires a non-empty 'sequence'")

    limit = int(query.get("limit", RESULTS_DEFAULT))
    window = int(query.get("context_window", WINDOW_DEFAULT))

    results: list[dict[str, Any]] = []
    scanned_games = 0

    for game_id, headers, contexts in iter_game_contexts(path):
        scanned_games += 1
        if not headers_match(headers, query):
            continue
        focus_color = game_focus_color(headers, query)
        if query.get("player") and focus_color is None:
            continue
        if query.get("color") in ("white", "black") and focus_color is None:
            continue

        candidates = sequence_matches(contexts, sequence, focus_color)
        motif_only = len(sequence) == 1 and not sequence[0].get("move") and not sequence[0].get("uci")
        if motif_only:
            candidates = collapse_motif_candidates(candidates)
        for cand in candidates:
            results.append(candidate_to_dict(cand, contexts, window=window))
            if len(results) >= limit:
                return {
                    "query": query,
                    "db_path": path,
                    "scanned_games": scanned_games,
                    "returned": len(results),
                    "results": results,
                }

    return {
        "query": query,
        "db_path": path,
        "scanned_games": scanned_games,
        "returned": len(results),
        "results": results,
    }


def load_query(path: str | None = None, inline_json: str | None = None) -> dict[str, Any]:
    if path and inline_json:
        raise QueryError("Use either query file or inline JSON, not both")
    if path:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    if inline_json:
        return json.loads(inline_json)
    raise QueryError("No query provided")
