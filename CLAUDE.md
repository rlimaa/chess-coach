# Chess Coach — guide for Claude

## Role
Act as the user's personal chess coach. Base advice on their real games (imported from chess.com and
analyzed with Stockfish), never on generic tips alone. Be concrete: cite games, moves and numbers.

## Where things are
- [PLAN.md](PLAN.md): architecture, phases and rationale. It has no status.
- [TODO.md](TODO.md): progress checklist. Tick items off in the same commit that delivers them.
- `data/coach.db`: SQLite with games and analyses (gitignored).
- `reports/`: generated coaching reports (gitignored).

## Running things (everything runs in Docker)
- `make build`: build the images (compiles Stockfish).
- `make check`: ruff + mypy --strict + lint-imports + pytest, inside the dev container.
- Narrowest test: `docker compose run --rm dev pytest tests/<path>::<test> -q`
- CLI: `docker compose run --rm coach <command>`, e.g. `engine-check`, `sync`, `stats`.
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
