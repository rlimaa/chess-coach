from markdown_it import MarkdownIt

from chesscoach.application.dto import (
    GameDetail,
    GameSummary,
    InsightsBundle,
    PeriodMetrics,
    ProgressReport,
    PuzzleExplanation,
    PuzzleResult,
    TrainingPlan,
    Variation,
)
from chesscoach.domain.entities import Game
from chesscoach.domain.insights import DayPart, EngineInsights
from chesscoach.domain.puzzles import Puzzle
from chesscoach.domain.services.classification import win_pct
from chesscoach.domain.services.statistics import ResultSummary
from chesscoach.domain.value_objects import Color, Evaluation


def summary(s: ResultSummary) -> dict[str, int | float]:
    return {
        "games": s.games,
        "wins": s.wins,
        "draws": s.draws,
        "losses": s.losses,
        "score_pct": s.score_pct,
    }


def insights(bundle: InsightsBundle) -> dict[str, object]:
    ins = bundle.insights
    result: dict[str, object] = {
        "time_class": ins.time_class.value,
        "overall": summary(ins.overall),
        "highlights": [
            {"text": h.text, "strength": h.strength, "severity": h.severity}
            for h in bundle.highlights
        ],
        "openings": [
            {"color": o.color.value, "family": o.family, **summary(o.summary)} for o in ins.openings
        ],
        "losses_by_termination": ins.losses_by_termination,
        "wins_by_termination": ins.wins_by_termination,
        "streaks": {
            "fresh": summary(ins.streaks.fresh),
            "after_win": summary(ins.streaks.after_win),
            "after_loss": summary(ins.streaks.after_loss),
            "after_two_plus_losses": summary(ins.streaks.after_two_plus_losses),
        },
        "by_session_position": [
            {"label": ls.label, **summary(ls.summary)} for ls in ins.by_session_position
        ],
        "by_day_part": [
            {"label": part.value, **summary(ins.by_day_part[part])} for part in DayPart
        ],
        "by_weekday": [{"label": ls.label, **summary(ls.summary)} for ls in ins.by_weekday],
        "by_rating_gap": [
            {
                "label": rgb.label,
                "expected_score_pct": rgb.expected_score_pct,
                **summary(rgb.summary),
            }
            for rgb in ins.by_rating_gap
        ],
        "rating_by_month": [
            {"month": f"{m.year:04d}-{m.month:02d}", "rating": m.rating, "games": m.games}
            for m in ins.rating_by_month
        ],
        "analyzed_games": ins.analyzed_games,
        "clock": None,
        "engine": None,
    }

    if ins.clock:
        result["clock"] = {
            "games": ins.clock.games,
            "in_trouble": summary(ins.clock.in_trouble),
            "not_in_trouble": summary(ins.clock.not_in_trouble),
            "losses": ins.clock.losses,
            "losses_on_time": ins.clock.losses_on_time,
        }

    if ins.engine:
        result["engine"] = _engine_insights(ins.engine)

    return result


def _engine_insights(ei: EngineInsights) -> dict[str, object]:
    result: dict[str, object] = {
        "games": ei.games,
        "accuracy": ei.accuracy,
        "opponent_accuracy": ei.opponent_accuracy,
        "by_phase": [
            {
                "phase": pe.phase.value,
                "moves": pe.moves,
                "avg_win_pct_loss": pe.avg_win_pct_loss,
                "inaccuracies": pe.inaccuracies,
                "mistakes": pe.mistakes,
                "blunders": pe.blunders,
                "serious_per_100": pe.serious_per_100,
            }
            for pe in ei.by_phase
        ],
        "time_pressure": None,
        "missed_mates": [
            {
                "game_url": m.game_url,
                "ply": m.ply,
                "san": m.san,
                "best_move_san": m.best_move_san,
            }
            for m in ei.missed_mates
        ],
        "punish_opportunities": ei.punish_opportunities,
        "unpunished": [
            {
                "game_url": m.game_url,
                "ply": m.ply,
                "san": m.san,
                "best_move_san": m.best_move_san,
            }
            for m in ei.unpunished
        ],
        "conversion": {
            "winning_games": ei.conversion.winning_games,
            "converted": ei.conversion.converted,
            "rate": ei.conversion.rate,
            "thrown": [
                {
                    "game_url": m.game_url,
                    "ply": m.ply,
                    "san": m.san,
                    "best_move_san": m.best_move_san,
                }
                for m in ei.conversion.thrown
            ],
        },
    }

    if ei.time_pressure:
        result["time_pressure"] = {
            "low_moves": ei.time_pressure.low_moves,
            "low_serious": ei.time_pressure.low_serious,
            "normal_moves": ei.time_pressure.normal_moves,
            "normal_serious": ei.time_pressure.normal_serious,
            "low_rate": ei.time_pressure.low_rate,
            "normal_rate": ei.time_pressure.normal_rate,
        }

    return result


def game(g: Game) -> dict[str, object]:
    return {
        "id": g.id,
        "url": g.url,
        "played_at": g.played_at.isoformat(),
        "time_class": g.time_class.value,
        "time_control": str(g.time_control),
        "rated": g.rated,
        "color": g.user_color.value,
        "rating": g.user.rating,
        "opponent": g.opponent.username,
        "opponent_rating": g.opponent.rating,
        "outcome": g.outcome.value,
        "termination": g.termination,
        "eco": g.eco,
        "opening": g.opening,
        "accuracy": g.user_accuracy,
    }


def game_summary(gs: GameSummary) -> dict[str, object]:
    result = game(gs.game)
    result["analyzed"] = gs.analyzed
    if gs.accuracy is not None:
        result["accuracy"] = gs.accuracy
    return result


def game_detail(gd: GameDetail) -> dict[str, object]:
    result = game(gd.game)
    result["pgn"] = gd.game.pgn

    positions: list[dict[str, int | str | None]] = []
    positions.append(
        {
            "ply": None,
            "san": None,
            "fen": gd.replay.plies[0].fen_before if gd.replay.plies else gd.replay.final_fen,
        }
    )
    for ply in gd.replay.plies:
        next_ply_idx = ply.index + 1
        next_ply = next((p for p in gd.replay.plies if p.index == next_ply_idx), None)
        fen_after = next_ply.fen_before if next_ply else gd.replay.final_fen
        positions.append(
            {
                "ply": ply.index,
                "san": ply.san,
                "fen": fen_after,
            }
        )

    analysis_data = None
    if gd.analysis:
        analysis_data = {
            "depth": gd.analysis.depth,
            "accuracy": {
                "user": gd.analysis.accuracy(gd.game.user_color),
                "opponent": gd.analysis.accuracy(gd.game.opponent_color),
            },
            "moves": [
                {
                    "ply": ma.ply,
                    "color": ma.color.value,
                    "san": ma.san,
                    "fen_before": ma.fen_before,
                    "phase": ma.phase.value,
                    "eval_before": _eval_dict(ma.eval_before),
                    "eval_after": _eval_dict(ma.eval_after),
                    "white_win_pct_after": win_pct(ma.eval_after, Color.WHITE),
                    "best_move_san": ma.best_move_san,
                    "win_pct_loss": ma.win_pct_loss,
                    "move_class": ma.move_class.value,
                    "clock_seconds": ma.clock_seconds,
                }
                for ma in gd.analysis.moves
            ],
        }

    return {
        "game": result,
        "positions": positions,
        "analysis": analysis_data,
    }


def _eval_dict(e: Evaluation) -> dict[str, int | None]:
    return {
        "cp": e.centipawns,
        "mate": e.mate_in,
    }


def puzzle(p: Puzzle) -> dict[str, object]:
    return {
        "id": p.id,
        "game_id": p.game_id,
        "game_url": p.game_url,
        "played_at": p.played_at.isoformat(),
        "time_class": p.time_class.value,
        "opponent": p.opponent,
        "ply": p.ply,
        "color": p.color.value,
        "fen": p.fen,
        "played_san": p.played_san,
        "mistake": p.mistake.value,
        "phase": p.phase.value,
        "win_pct_loss": p.win_pct_loss,
    }


def puzzle_result(pr: PuzzleResult) -> dict[str, bool | str | None]:
    result = {
        "legal": pr.legal,
        "correct": pr.correct,
        "answer_san": pr.answer_san,
        "solution_san": None,
    }
    if pr.legal:
        result["solution_san"] = pr.solution_san
    return result


def progress(p: ProgressReport) -> dict[str, object]:
    return {
        "time_class": p.time_class.value,
        "days": p.days,
        "current": _period_metrics(p.current),
        "previous": _period_metrics(p.previous),
    }


def _period_metrics(pm: PeriodMetrics) -> dict[str, int | float | None]:
    return {
        "games": pm.games,
        "score_pct": pm.score_pct,
        "rating_change": pm.rating_change,
        "time_trouble_pct": pm.time_trouble_pct,
        "losses_on_time_pct": pm.losses_on_time_pct,
        "analyzed_games": pm.analyzed_games,
        "accuracy": pm.accuracy,
        "serious_per_100": pm.serious_per_100,
    }


# Raw HTML stays disabled: the plan is rendered as text even if it contains tags.
_MARKDOWN = MarkdownIt("commonmark", {"html": False}).enable("table")


def training_plan(plan: TrainingPlan) -> dict[str, object]:
    return {"html": _MARKDOWN.render(plan.markdown), "updated_at": plan.updated_at.isoformat()}


def _variation(line: Variation) -> dict[str, object]:
    return {
        "eval": {"cp": line.evaluation.centipawns, "mate": line.evaluation.mate_in},
        "moves": [{"san": m.san, "fen": m.fen_after} for m in line.moves],
    }


def explanation(explained: PuzzleExplanation) -> dict[str, object]:
    return {
        "best": _variation(explained.best),
        "attempted": _variation(explained.attempted) if explained.attempted else None,
    }
