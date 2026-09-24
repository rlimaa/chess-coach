import pytest

from chesscoach.domain.services.engine_insights import engine_insights
from chesscoach.domain.value_objects import (
    Color,
    Evaluation,
    MoveClass,
    Outcome,
    Phase,
    TimeClass,
    TimeControl,
)
from tests.builders import make_analysis, make_game, make_move

ME, THEM = Color.WHITE, Color.BLACK
BLITZ = TimeControl.parse("300")


def test_no_analyzed_games_means_no_engine_insights() -> None:
    assert engine_insights([]) is None


def test_counts_only_the_users_moves_per_phase() -> None:
    game = make_game(user_color=ME)
    analysis = make_analysis(
        game,
        make_move(color=ME, phase=Phase.OPENING, win_pct_loss=2.0, move_class=MoveClass.GOOD),
        make_move(color=THEM, phase=Phase.OPENING, win_pct_loss=40.0, move_class=MoveClass.BLUNDER),
        make_move(color=ME, phase=Phase.ENDGAME, win_pct_loss=20.0, move_class=MoveClass.BLUNDER),
        make_move(color=ME, phase=Phase.ENDGAME, win_pct_loss=-3.0, move_class=MoveClass.BEST),
    )

    insights = engine_insights([(game, analysis)])

    assert insights is not None
    assert insights.games == 1
    phases = {p.phase: p for p in insights.by_phase}
    assert list(phases) == [Phase.OPENING, Phase.MIDDLEGAME, Phase.ENDGAME]
    assert (phases[Phase.OPENING].moves, phases[Phase.OPENING].blunders) == (1, 0)
    assert phases[Phase.MIDDLEGAME].moves == 0
    endgame = phases[Phase.ENDGAME]
    assert (endgame.moves, endgame.blunders) == (2, 1)
    assert endgame.avg_win_pct_loss == pytest.approx(10.0)
    assert endgame.serious_per_100 == pytest.approx(50.0)


def test_accuracy_is_averaged_over_games_for_both_sides() -> None:
    game = make_game(user_color=ME)
    analysis = make_analysis(
        game,
        make_move(color=ME, win_pct_loss=0.0),
        make_move(color=THEM, win_pct_loss=30.0, move_class=MoveClass.BLUNDER),
    )

    insights = engine_insights([(game, analysis)])

    assert insights is not None
    assert insights.accuracy == 100.0
    assert insights.opponent_accuracy is not None
    assert insights.opponent_accuracy < 60


def test_time_pressure_compares_error_rates_below_ten_percent_of_the_clock() -> None:
    game = make_game(user_color=ME, time_control=BLITZ)
    analysis = make_analysis(
        game,
        make_move(color=ME, clock_seconds=200.0),
        make_move(color=THEM, clock_seconds=10.0),
        make_move(color=ME, clock_seconds=25.0, move_class=MoveClass.BLUNDER, win_pct_loss=30.0),
        make_move(color=ME, clock_seconds=20.0),
    )

    insights = engine_insights([(game, analysis)])

    assert insights is not None
    pressure = insights.time_pressure
    assert pressure is not None
    assert (pressure.low_moves, pressure.low_serious) == (2, 1)
    assert (pressure.normal_moves, pressure.normal_serious) == (1, 0)
    assert pressure.low_rate == 50.0


def test_correspondence_games_have_no_time_pressure() -> None:
    game = make_game(
        time_class=TimeClass.DAILY, time_control=TimeControl.parse("1/86400"), user_color=ME
    )
    analysis = make_analysis(game, make_move(color=ME, clock_seconds=100.0))

    insights = engine_insights([(game, analysis)])

    assert insights is not None
    assert insights.time_pressure is None


def test_a_forced_mate_that_the_user_let_slip_is_a_missed_mate() -> None:
    game = make_game(user_color=THEM, url="https://chess.com/game/1")
    analysis = make_analysis(
        game,
        make_move(color=ME),
        make_move(
            color=THEM,
            san="Qd1",
            best_move_san="Qh2#",
            eval_before=Evaluation.mate(-1),
            eval_after=Evaluation.cp(-300),
            move_class=MoveClass.MISTAKE,
            win_pct_loss=12.0,
        ),
        make_move(color=ME),
        make_move(color=THEM, eval_before=Evaluation.mate(-2), eval_after=Evaluation.mate(-1)),
    )

    insights = engine_insights([(game, analysis)])

    assert insights is not None
    (missed,) = insights.missed_mates
    assert (missed.game_url, missed.ply, missed.san, missed.best_move_san) == (
        "https://chess.com/game/1",
        1,
        "Qd1",
        "Qh2#",
    )


def test_replies_to_opponent_blunders_are_opportunities_to_punish() -> None:
    game = make_game(user_color=ME)
    analysis = make_analysis(
        game,
        make_move(color=ME),
        make_move(color=THEM, move_class=MoveClass.BLUNDER, win_pct_loss=25.0),
        make_move(color=ME, san="a3", move_class=MoveClass.MISTAKE, win_pct_loss=11.0),
        make_move(color=THEM, move_class=MoveClass.BLUNDER, win_pct_loss=25.0),
        make_move(color=ME, move_class=MoveClass.BEST),
    )

    insights = engine_insights([(game, analysis)])

    assert insights is not None
    assert insights.punish_opportunities == 2
    assert [m.san for m in insights.unpunished] == ["a3"]


def test_conversion_tracks_games_where_the_user_was_clearly_winning() -> None:
    winning = [make_move(color=ME, eval_before=Evaluation.cp(500), san="Nf3")]
    won = make_game(id="won", user_color=ME, outcome=Outcome.WIN)
    thrown = make_game(id="thrown", user_color=ME, outcome=Outcome.DRAW, url="u/thrown")
    never_winning = make_game(id="even", user_color=ME, outcome=Outcome.LOSS)

    insights = engine_insights(
        [
            (won, make_analysis(won, *winning)),
            (thrown, make_analysis(thrown, *winning)),
            (never_winning, make_analysis(never_winning, make_move(color=ME))),
        ]
    )

    assert insights is not None
    conversion = insights.conversion
    assert (conversion.winning_games, conversion.converted) == (2, 1)
    assert conversion.rate == 50.0
    assert [m.game_url for m in conversion.thrown] == ["u/thrown"]


def test_choosing_a_safe_winning_move_over_a_long_mate_is_not_a_missed_mate() -> None:
    game = make_game(user_color=ME)
    analysis = make_analysis(
        game,
        make_move(
            color=ME,
            eval_before=Evaluation.mate(9),
            eval_after=Evaluation.cp(1500),
            move_class=MoveClass.GOOD,
            win_pct_loss=0.4,
        ),
    )

    insights = engine_insights([(game, analysis)])

    assert insights is not None
    assert insights.missed_mates == ()
