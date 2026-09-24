import hashlib
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from chesscoach.application.errors import GameNotFoundError, PuzzleNotFoundError
from chesscoach.container import Container
from chesscoach.domain.value_objects import TimeClass
from chesscoach.interfaces.web import serializers


class AnswerModel(BaseModel):
    move: str


def create_app(container: Container) -> FastAPI:
    username = container.settings.chesscom_username
    if not username:
        raise ValueError("CHESSCOM_USERNAME is required")

    app = FastAPI()

    @app.get("/api/meta")
    def get_meta() -> dict[str, object]:
        by_class = container.get_stats().execute(username).by_time_class
        ranked = sorted(by_class.items(), key=lambda item: item[1].summary.games, reverse=True)
        return {
            "username": username,
            "time_classes": [
                {"time_class": tc.value, "games": stats.summary.games} for tc, stats in ranked
            ],
        }

    @app.get("/api/insights/{time_class}")
    def get_insights(time_class: TimeClass) -> dict[str, object]:
        bundle = container.build_insights().execute(username, time_class)
        if bundle is None:
            raise HTTPException(status_code=404, detail="No games in this time class")
        return serializers.insights(bundle)

    @app.get("/api/games")
    def list_games(
        time_class: TimeClass | None = None, limit: int = 50, offset: int = 0
    ) -> list[dict[str, object]]:
        summaries = container.recent_games().execute(
            username, time_class=time_class, limit=limit, offset=offset
        )
        return [serializers.game_summary(gs) for gs in summaries]

    @app.get("/api/games/{reference:path}")
    def get_game(reference: str) -> dict[str, object]:
        try:
            detail = container.show_game().execute(reference)
        except GameNotFoundError as e:
            raise HTTPException(status_code=404, detail="Game not found") from e
        return serializers.game_detail(detail)

    @app.get("/api/puzzles")
    def list_puzzles(
        time_class: TimeClass | None = None, limit: int = 10
    ) -> list[dict[str, object]]:
        puzzles = container.next_puzzles().execute(username, time_class=time_class, limit=limit)
        return [serializers.puzzle(p) for p in puzzles]

    @app.post("/api/puzzles/{puzzle_id}/answer")
    def answer_puzzle(puzzle_id: str, body: AnswerModel) -> dict[str, bool | str | None]:
        try:
            puzzle = container.find_puzzle().execute(puzzle_id)
        except PuzzleNotFoundError as e:
            raise HTTPException(status_code=404, detail="Puzzle not found") from e
        result = container.solve_puzzle().execute(puzzle, body.move)
        return serializers.puzzle_result(result)

    @app.get("/api/progress/{time_class}")
    def get_progress(time_class: TimeClass, days: int = 30) -> dict[str, object]:
        report = container.compare_progress().execute(username, time_class, days)
        return serializers.progress(report)

    @app.middleware("http")
    async def revalidate_static(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        if request.url.path == "/" or request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache"
        return response

    @app.get("/api/training-plan")
    def get_training_plan() -> dict[str, object]:
        plan = container.get_training_plan().execute()
        if plan is None:
            raise HTTPException(status_code=404, detail="No training plan yet")
        return serializers.training_plan(plan)

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir, check_dir=False), name="static")

    @app.get("/")
    def get_dashboard() -> HTMLResponse:
        return HTMLResponse(_versioned_index(static_dir))

    return app


def _versioned_index(static_dir: Path) -> str:
    """Stamp asset URLs with a content hash so browsers never run a stale script."""
    html = (static_dir / "index.html").read_text()
    for asset in ("app.js", "styles.css"):
        digest = hashlib.sha256((static_dir / asset).read_bytes()).hexdigest()[:12]
        html = html.replace(f'/static/{asset}"', f'/static/{asset}?v={digest}"')
    return html
