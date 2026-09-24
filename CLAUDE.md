# Chess Coach — guide for Claude

## Role
Act as the user's personal chess coach. Base advice on their real games (imported from chess.com and
analyzed with Stockfish), never on generic tips alone. Be concrete: cite games, moves and numbers.

## Where things are
- [PLAN.md](PLAN.md): architecture, phases and rationale. It has no status.
- [TODO.md](TODO.md): progress checklist. Tick items off in the same commit that delivers them.
- `data/coach.db`: SQLite with games and analyses (gitignored).
- `reports/`: generated coaching reports (gitignored).

## Coaching workflow
Personal coaching files live in `coaching/` (gitignored): `training_plan.md` and `checkins/<date>.md`.

When the user asks for coaching, a check-in or "what should I work on":
1. `make sync`, then `docker compose run --rm coach report` (rapid + blitz). Read both reports in
   `reports/`. They are the source of truth; cite their numbers.
2. `docker compose run --rm coach progress -t <class> --days 30` for each time class to see trends
   since the last check-in.
3. For engine findings, open the linked games and `coach game <url>` to look at concrete moments.
4. Update `coaching/training_plan.md`. Keep it short:
   - Goals: 2-3 measurable targets per time class, e.g. "blitz: losses on time < 20%".
   - This week's focus: one or two themes taken from the report's "Work on" list.
   - Drills: `coach puzzles -t <class>` sessions (they come from the user's own mistakes), plus
     specific habits such as a clock rule or which opening line to study.
   - Log: date and a one-line result of each check-in.
5. Write the check-in summary to `coaching/checkins/<date>.md` and tell the user the 3 most
   important points.

Prefer few, concrete, measurable changes over long advice lists. Reuse `coach puzzles --list`
to talk through specific positions (never reveal a solution before the user tries it).

## Running things (everything runs in Docker)
- `make build`: build the images (compiles Stockfish).
- `make check`: ruff + mypy --strict + lint-imports + pytest, inside the dev container.
- Narrowest test: `docker compose run --rm dev pytest tests/<path>::<test> -q`
- CLI: `docker compose run --rm coach <command>`: `engine-check`, `sync`, `stats`, `analyze`,
  `game`, `report`, `puzzles`, `progress`, `web` (dashboard: `make web`, http://localhost:8000).
- `make lock`: refresh `uv.lock` after changing dependencies in `pyproject.toml`.

## Architecture rules (Clean Architecture, enforced by `lint-imports`)
Dependencies point inward only:
`interfaces → container → config → adapters → application → domain`

- `domain/`: entities, value objects and pure services. No I/O, no frameworks. Immutable
  `@dataclass(frozen=True, slots=True)`.
- `application/`: use cases (one public `execute()` each) and ports (`typing.Protocol`) in
  `ports.py`. It must not import httpx, typer, rich or pydantic_settings.
- `adapters/`: implementations of ports (chess.com HTTP, Stockfish, SQLite, Markdown). Adapters
  receive plain values through their constructors and never read `config`.
- `container.py`: the composition root, the only place where concrete adapters are built and wired
  into use cases.
- `interfaces/`: CLI (Typer) now, web (FastAPI) later. Formatting only, no business logic.

## Development workflow: TDD
All feature work follows the `tdd` skill in `.claude/skills/tdd/SKILL.md`:
RED (one failing test) → GREEN (the smallest code that passes) → REFACTOR (only when green).
- Test behavior through public interfaces: use case `execute()`, domain services, CLI commands.
- Use test doubles only at port boundaries (fakes in `tests/fakes.py`). Never mock internals.
- Adapters get integration tests: SQLite in `tmp_path`, chess.com via recorded fixtures + respx,
  and the real Stockfish marked `@pytest.mark.slow`.

## Git
- One commit per phase on `main`, message `Phase N: <title>`, pushed only after `make check`
  passes. Update TODO.md in that same commit.
