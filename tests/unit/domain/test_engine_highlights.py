from dataclasses import replace
from typing import Any

from chesscoach.domain.insights import (
    Conversion,
    EngineInsights,
    MomentRef,
    PhaseErrors,
    TimePressureErrors,
)
from chesscoach.domain.services.highlights import find_highlights
from chesscoach.domain.value_objects import Phase
from tests.builders import make_insights

MOMENT = MomentRef("u", 10, "Qd1", "Qh2#")
QUIET_PHASES = (
    PhaseErrors(Phase.OPENING, 400, 1.0, 10, 4, 4),
    PhaseErrors(Phase.MIDDLEGAME, 800, 2.0, 30, 16, 16),
    PhaseErrors(Phase.ENDGAME, 300, 2.0, 10, 6, 6),
)


HEALTHY = EngineInsights(
    games=50,
    accuracy=80.0,
    opponent_accuracy=78.0,
    by_phase=QUIET_PHASES,
    time_pressure=TimePressureErrors(40, 2, 2000, 80),
    missed_mates=(),
    punish_opportunities=20,
    unpunished=(MOMENT,) * 2,
    conversion=Conversion(winning_games=20, converted=17, thrown=()),
)


def _engine(**overrides: Any) -> EngineInsights:
    return replace(HEALTHY, **overrides)


def _texts(engine: EngineInsights) -> list[str]:
    return [h.text for h in find_highlights(make_insights(engine=engine))]


def test_a_healthy_engine_profile_adds_nothing() -> None:
    assert _texts(_engine()) == []


def test_flags_the_phase_where_serious_errors_concentrate() -> None:
    phases = (*QUIET_PHASES[:2], PhaseErrors(Phase.ENDGAME, 300, 6.0, 10, 15, 15))

    (text,) = _texts(_engine(by_phase=phases))

    assert "endgame" in text
    assert "10.0 per 100 moves" in text


def test_flags_errors_under_time_pressure() -> None:
    (text,) = _texts(_engine(time_pressure=TimePressureErrors(50, 15, 2000, 80)))

    assert "30%" in text
    assert "4%" in text


def test_flags_missed_mates_and_unpunished_blunders() -> None:
    texts = _texts(_engine(missed_mates=(MOMENT,) * 4, unpunished=(MOMENT,) * 9))

    assert any("missed 4 forced mates" in t for t in texts)
    assert any("45%" in t and "blunder" in t for t in texts)


def test_conversion_is_a_weakness_when_low_and_a_strength_when_high() -> None:
    (weak,) = find_highlights(
        make_insights(engine=_engine(conversion=Conversion(20, 12, (MOMENT,) * 8)))
    )
    (strong,) = find_highlights(make_insights(engine=_engine(conversion=Conversion(20, 19, ()))))

    assert not weak.strength
    assert "60%" in weak.text
    assert strong.strength
    assert "95%" in strong.text
