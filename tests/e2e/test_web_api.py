import json
import re
from collections.abc import Iterator
from pathlib import Path

import pytest
import respx
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from chesscoach.adapters.persistence.sqlite.analysis_repository import SqliteAnalysisRepository
from chesscoach.adapters.persistence.sqlite.database import SqliteDatabase
from chesscoach.config import load_settings
from chesscoach.container import Container
from chesscoach.domain.value_objects import Color, Evaluation, MoveClass
from chesscoach.interfaces.cli.main import app as cli
from chesscoach.interfaces.web.app import create_app
from tests.builders import make_analysis, make_game, make_move
from tests.fixtures.chesscom import load, month_game

API = "https://api.chess.com/pub/player"
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BLITZ = month_game(0)
SUMMARY_KEYS = {"games", "wins", "draws", "losses", "score_pct"}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
    db_path = tmp_path / "coach.db"
    monkeypatch.setenv("COACH_CONFIG", str(tmp_path / "none.toml"))
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("CHESSCOM_USERNAME", "rodigola")
    monkeypatch.setenv("TRAINING_PLAN_PATH", str(tmp_path / "coaching" / "training_plan.md"))
    monkeypatch.setenv("REPERTOIRE_PATH", str(tmp_path / "coaching" / "repertoire.json"))
    with respx.mock:
        respx.get(f"{API}/rodigola/games/archives").respond(
            json={"archives": [f"{API}/rodigola/games/2026/09"]}
        )
        respx.get(f"{API}/rodigola/games/2026/09").respond(json=load("month.json"))
        CliRunner().invoke(cli, ["sync"])
    moves = (
        make_move(
            color=Color.WHITE,
            fen_before=START,
            san="a3",
            best_move_san="e4",
            eval_after=Evaluation.cp(-150),
            move_class=MoveClass.BLUNDER,
            win_pct_loss=20.0,
        ),
        make_move(
            color=Color.BLACK,
            san="e5",
            eval_before=Evaluation.cp(-150),
            eval_after=Evaluation.mate(-3),
        ),
    )
    SqliteAnalysisRepository(SqliteDatabase(db_path)).save(
        make_analysis(make_game(id=BLITZ["uuid"]), *moves)
    )
    with TestClient(create_app(Container(load_settings()))) as test_client:
        yield test_client


def test_meta_lists_the_player_and_time_classes_by_games(client: TestClient) -> None:
    meta = client.get("/api/meta").json()

    assert meta["username"] == "rodigola"
    assert {t["time_class"]: t["games"] for t in meta["time_classes"]} == {
        "blitz": 2,
        "rapid": 2,
        "bullet": 1,
        "daily": 1,
    }


def test_insights_expose_every_section_with_summaries(client: TestClient) -> None:
    body = client.get("/api/insights/blitz").json()

    assert body["time_class"] == "blitz"
    assert set(body["overall"]) == SUMMARY_KEYS
    assert body["analyzed_games"] == 1
    assert body["engine"] is None
    for key in ("openings", "by_session_position", "by_day_part", "by_weekday", "by_rating_gap"):
        assert isinstance(body[key], list)
    assert set(body["by_rating_gap"][0]) == {"label", "expected_score_pct", *SUMMARY_KEYS}
    assert set(body["streaks"]) == {"fresh", "after_win", "after_loss", "after_two_plus_losses"}
    assert body["rating_by_month"][0].keys() == {"month", "rating", "games"}
    assert all(set(h) == {"text", "strength", "severity"} for h in body["highlights"])


def test_insights_need_games_of_a_valid_time_class(client: TestClient) -> None:
    assert client.get("/api/insights/nonsense").status_code == 422


def test_games_list_is_newest_first_with_analysis_flag(client: TestClient) -> None:
    games = client.get("/api/games", params={"time_class": "blitz", "limit": 10}).json()

    first = games[0]
    assert first["id"] == BLITZ["uuid"]
    assert first["analyzed"] is True
    assert first["color"] == "white"
    expected = {"url", "played_at", "opponent", "opponent_rating", "rating", "outcome", "accuracy"}
    assert expected <= set(first)


def test_game_detail_has_positions_and_analysis(client: TestClient) -> None:
    body = client.get(f"/api/games/{BLITZ['uuid']}").json()

    game, positions, analysis = body["game"], body["positions"], body["analysis"]
    assert game["id"] == BLITZ["uuid"]
    assert positions[0]["fen"] == START
    assert positions[0]["san"] is None
    assert positions[1]["san"] == "e4"
    assert positions[1]["fen"] != START
    first, second = analysis["moves"]
    assert first["move_class"] == "blunder"
    assert first["best_move_san"] == "e4"
    assert first["eval_after"] == {"cp": -150, "mate": None}
    assert 0 < first["white_win_pct_after"] < 50
    assert second["white_win_pct_after"] == 0.0
    assert analysis["depth"] == 12


def test_unknown_game_is_404(client: TestClient) -> None:
    assert client.get("/api/games/nope").status_code == 404


def test_puzzles_hide_the_solution_until_answered(client: TestClient) -> None:
    (puzzle,) = client.get("/api/puzzles", params={"time_class": "blitz"}).json()

    assert puzzle["fen"] == START
    assert puzzle["played_san"] == "a3"
    assert puzzle["game_id"] == BLITZ["uuid"]
    assert puzzle["ply"] == 0
    assert "solution_san" not in puzzle

    illegal = client.post(f"/api/puzzles/{puzzle['id']}/answer", json={"move": "Ke5"}).json()
    right = client.post(f"/api/puzzles/{puzzle['id']}/answer", json={"move": "e2e4"}).json()

    assert illegal == {"legal": False, "correct": False, "answer_san": None, "solution_san": None}
    assert right == {"legal": True, "correct": True, "answer_san": "e4", "solution_san": "e4"}
    assert client.get("/api/puzzles", params={"time_class": "blitz"}).json() == []


def test_answering_an_unknown_puzzle_is_404(client: TestClient) -> None:
    assert client.post("/api/puzzles/nope:1/answer", json={"move": "e4"}).status_code == 404


def test_progress_compares_two_periods(client: TestClient) -> None:
    body = client.get("/api/progress/blitz", params={"days": 3650}).json()

    assert body["days"] == 3650
    assert body["current"]["games"] == 2
    assert {"score_pct", "rating_change", "time_trouble_pct", "accuracy"} <= set(body["previous"])


def test_dashboard_page_is_served(client: TestClient) -> None:
    page = client.get("/")

    assert page.status_code == 200
    assert "<title>" in page.text
    script = client.get("/static/app.js")
    assert script.status_code == 200
    assert script.headers["cache-control"] == "no-cache"


def test_game_detail_accepts_the_full_chesscom_url(client: TestClient) -> None:
    response = client.get(f"/api/games/{BLITZ['url']}")

    assert response.status_code == 200
    assert response.json()["game"]["id"] == BLITZ["uuid"]


def test_dashboard_assets_are_versioned_so_updates_are_never_cached(client: TestClient) -> None:
    page = client.get("/").text

    script = re.search(r'src="(/static/app\.js\?v=[0-9a-f]{12})"', page)
    style = re.search(r'href="(/static/styles\.css\?v=[0-9a-f]{12})"', page)
    assert script is not None
    assert style is not None
    assert client.get(script.group(1)).status_code == 200


def test_training_plan_is_rendered_from_markdown(client: TestClient, tmp_path: Path) -> None:
    plan = tmp_path / "coaching" / "training_plan.md"
    plan.parent.mkdir()
    plan.write_text(
        "# Training plan\n\n## This week's focus\n1. **Blitz clock rule**\n\n"
        "| Goal | Now |\n|---|---|\n| Losses on time < 20% | 30% |\n\n<script>alert(1)</script>\n"
    )

    body = client.get("/api/training-plan").json()

    assert "<h1>Training plan</h1>" in body["html"]
    assert "<strong>Blitz clock rule</strong>" in body["html"]
    assert "<table>" in body["html"]
    assert "<script>" not in body["html"]
    assert body["updated_at"]


def test_missing_training_plan_is_404(client: TestClient) -> None:
    assert client.get("/api/training-plan").status_code == 404


@pytest.fixture
def shallow_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENGINE__EXPLAIN_DEPTH", "8")


def _puzzle_id(client: TestClient) -> str:
    puzzle_id: str = client.get("/api/puzzles", params={"time_class": "blitz"}).json()[0]["id"]
    return puzzle_id


@pytest.mark.slow
@pytest.mark.usefixtures("shallow_engine")
def test_explanation_shows_best_and_attempted_lines_after_a_wrong_answer(
    client: TestClient,
) -> None:
    puzzle_id = _puzzle_id(client)
    explanation_url = f"/api/puzzles/{puzzle_id}/explanation"
    assert client.get(explanation_url, params={"move": "d4"}).status_code == 409

    client.post(f"/api/puzzles/{puzzle_id}/answer", json={"move": "d4"})
    body = client.get(explanation_url, params={"move": "d4"}).json()

    assert body["best"]["moves"][0]["san"] == "e4"
    assert body["attempted"]["moves"][0]["san"] == "d4"
    assert set(body["best"]["moves"][0]) == {"san", "fen"}
    assert set(body["best"]["eval"]) == {"cp", "mate"}


@pytest.mark.slow
@pytest.mark.usefixtures("shallow_engine")
def test_explanation_after_the_right_answer_has_only_the_best_line(client: TestClient) -> None:
    puzzle_id = _puzzle_id(client)
    client.post(f"/api/puzzles/{puzzle_id}/answer", json={"move": "e4"})

    body = client.get(f"/api/puzzles/{puzzle_id}/explanation", params={"move": "e2e4"}).json()

    assert body["attempted"] is None
    assert (
        client.get(f"/api/puzzles/{puzzle_id}/explanation", params={"move": "Ke5"}).status_code
        == 422
    )


def _write_repertoire(tmp_path: Path, line: str) -> None:
    path = tmp_path / "coaching" / "repertoire.json"
    path.parent.mkdir(exist_ok=True)
    entry = {
        "id": "black-italian",
        "title": "Black vs the Italian: 3...Bc5",
        "side": "black",
        "focus": True,
        "line": line,
        "key_ply": 5,
        "why": "3...Nf6 scored 14%",
        "plan": "...d6, ...Nf6, ...0-0",
        "instead_of": "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5",
        "instead_result": "14% in 7 games",
    }
    path.write_text(json.dumps({"lines": [entry]}))


def test_openings_show_each_repertoire_line_with_board_positions(
    client: TestClient, tmp_path: Path
) -> None:
    _write_repertoire(tmp_path, "e4 e5 Nf3 Nc6 Bc4 Bc5")

    (opening,) = client.get("/api/openings").json()

    assert opening["id"] == "black-italian"
    assert opening["side"] == "black"
    assert opening["key_ply"] == 5
    assert opening["moves"][5] == {
        "san": "Bc5",
        "fen": "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    }
    assert [m["san"] for m in opening["old_moves"]][-1] == "Ng5"
    assert opening["instead_result"] == "14% in 7 games"


def test_no_repertoire_file_means_no_openings(client: TestClient) -> None:
    assert client.get("/api/openings").json() == []


def test_a_broken_repertoire_line_is_reported(client: TestClient, tmp_path: Path) -> None:
    _write_repertoire(tmp_path, "e4 e5 Nf6 Nc6 Bc4 Bc5")

    response = client.get("/api/openings")

    assert response.status_code == 422
    assert "black-italian" in response.json()["detail"]
