# Chess Coach — Plan

> Progress is tracked in [TODO.md](TODO.md). This file describes *what* and *why*; it has no status.

## Context
New personal project in the empty folder `/Users/admin/Documents/Chess`. Goal: turn Claude into a personal chess coach that knows your actual games. We pull your games from chess.com, analyze them with a chess engine, find recurring weaknesses, and build an improvement plan from them. You chat with Claude here. The CLI and a small data store give Claude facts to work from. A web dashboard comes in a later phase.

Decisions: **Python**, **self-hosted Stockfish**, **CLI first, dashboard later**, **Clean Architecture**, **TDD**, **everything in Docker**. The chess.com username goes in `.env` / `config.toml`.

## Research findings
**chess.com Published-Data API**: free, read-only, no auth.
- `GET https://api.chess.com/pub/player/{user}` returns your profile. `/stats` returns ratings per time control.
- `/games/archives` lists the monthly archive URLs. `/games/{YYYY}/{MM}` returns that month's games as JSON with PGN, clocks, accuracies and ECO.
- Limits: serial requests are unlimited, but parallel requests can get a 429. They ask for a User-Agent that includes contact info. Responses support ETag/304, so re-syncs are cheap.

**Chess engine options**:
| Option | Cost | Strength / limits | Use |
|---|---|---|---|
| **Stockfish 19, self-hosted** (built into the Docker image, GPLv3) | free | full strength, unlimited, offline | **primary** |
| chess-api.com (REST/WebSocket, Stockfish 18) | free tier | depth ≤12, 50 ms per move | not needed; optional later for a web UI |
| Lichess `/api/cloud-eval` | free | returns evals only for positions already in its cache | possible opening-phase shortcut later |
| Stockfish WASM (stockfish.js) | free | runs in the browser | Phase 5 dashboard board |

Key library: **python-chess**. It parses PGN, handles board logic and controls Stockfish over UCI (`chess.engine.SimpleEngine`).

## Architecture: Clean Architecture
**Dependency rule:** source code depends only inward: `interfaces → adapters → application → domain`. The domain and application layers never import `httpx`, `sqlite3`, `typer` or the Stockfish process. They talk to the outside world only through **ports**, which are `typing.Protocol` interfaces. Concrete **adapters** implement those ports. A single **composition root** wires everything together. This way you can swap chess.com for Lichess, SQLite for Postgres, or CLI for the web without touching business logic, and use cases can be unit-tested with in-memory fakes.

```
Chess/
  pyproject.toml              # deps + tooling config (ruff, mypy --strict, pytest, import-linter)
  config.toml                 # username, contact email, engine path/depth/threads, db path
  CLAUDE.md                   # coaching role + architecture rules + how to query data
  src/chesscoach/
    domain/                   # pure Python, no I/O, no 3rd-party deps except python-chess types where unavoidable
      entities.py             # Game, Move, Player, GameAnalysis, MoveAnalysis (frozen dataclasses)
      value_objects.py        # Evaluation (cp|mate), WinProbability, TimeControl, Color, Phase, MoveClass
      services/
        classification.py     # eval → win% (Lichess formula), win%-drop → MoveClass, accuracy
        phase_detection.py    # opening/middlegame/endgame by material/ply
        weakness_detection.py # recurring-pattern rules → Weakness objects
    application/
      ports.py                # Protocols: GameSource, GameRepository, AnalysisRepository,
                              #   PositionEngine, ReportWriter, Clock
      dto.py                  # input/output data for use cases
      use_cases/
        sync_games.py         # SyncGames(source, repo).execute(username)
        analyze_games.py      # AnalyzeGames(repo, engine, analysis_repo).execute(limit)
        get_stats.py
        detect_weaknesses.py
        generate_report.py
        build_puzzles.py
    adapters/                 # (infrastructure) implements ports
      chesscom/
        client.py             # httpx, User-Agent, serial requests, 429 backoff, ETag cache
        mapper.py             # chess.com JSON → domain Game (anti-corruption layer)
      engine/
        stockfish_engine.py   # python-chess UCI → PositionEngine, FEN eval cache
      persistence/
        sqlite/
          schema.sql / migrations
          game_repository.py
          analysis_repository.py
      reporting/
        markdown_report_writer.py
    interfaces/               # delivery mechanisms
      cli/
        main.py               # Typer: `coach sync | analyze | stats | report | puzzles | game <id>`
        presenters.py         # rich tables; formatting only
      web/                    # Phase 5 (FastAPI) — reuses the same use cases
    config.py                 # load & validate config.toml (pydantic)
    container.py              # composition root: builds adapters, injects into use cases
  tests/
    unit/domain/              # pure logic, no fakes needed
    unit/application/         # use cases with in-memory fakes of ports (tests/fakes.py)
    integration/adapters/     # SQLite in tmp dir, chess.com via recorded JSON fixtures, real Stockfish (marked slow)
    e2e/                      # CLI via Typer CliRunner
  data/coach.db               # gitignored
  reports/
```

## Containerization (Docker)
Everything runs in Docker, so a new machine only needs Docker installed. You don't need Python or Stockfish on the host.

```
Chess/
  Dockerfile            # multi-stage
  docker-compose.yml
  .dockerignore
  Makefile              # thin wrappers: make build | sync | analyze | stats | report | test | lint | shell
```
- **Dockerfile** (multi-stage):
  1. `stockfish-builder` (debian-slim + build-essential) clones the Stockfish release tag pinned by build arg `STOCKFISH_VERSION`. It runs `make -j build ARCH=$SF_ARCH`, where `SF_ARCH` comes from `TARGETARCH`: `armv8` on Apple Silicon/arm64, `x86-64-avx2` on amd64. This makes the build portable across Mac and Linux, which the Debian apt package (usually outdated) or an x86-only binary would not be.
  2. `base` (`python:3.13-slim`) copies `/usr/local/bin/stockfish` from the builder, installs **uv**, and installs dependencies from `uv.lock` for reproducible builds. It runs as a non-root user.
  3. `dev` target adds dev dependencies (ruff, mypy, pytest, import-linter) and is used for tests and lint.
  4. `runtime` target has the entrypoint `coach`.
- **docker-compose.yml** has two services:
  - `coach`: the runtime image. Volumes: `./data:/app/data` (SQLite), `./reports:/app/reports`, `./config.toml:/app/config.toml:ro`. It uses `env_file: .env` for `CHESSCOM_USERNAME` and `CONTACT_EMAIL`, which override config values.
  - `dev`: the dev target with `./:/app` bind-mounted, for tests and lint.
- **Usage:** `docker compose run --rm coach sync`, `... coach analyze --last 50`, or the matching `make` shortcuts. Engine threads and hash are configurable through env vars so they can use the container's CPUs.
- **Phase 5** adds a `web` service (FastAPI + uvicorn) to the same compose file, using the same image and volumes.
- **CI-ready:** `docker compose run --rm dev make check` runs ruff, mypy, import-linter and pytest.
- **Config precedence:** env vars > `config.toml` > defaults, implemented in `config.py` with pydantic-settings. The Stockfish path defaults to `/usr/local/bin/stockfish`.

**Code quality guardrails**
- `ruff` (lint + format), `mypy --strict`, `pytest` + coverage.
- **import-linter** contracts enforce the layer rules in CI, e.g. "domain must not import application/adapters/interfaces".
- `pre-commit` hooks run ruff, mypy and import-linter.
- Domain objects are immutable (`@dataclass(frozen=True, slots=True)`), with explicit types everywhere and no global state. Dependencies are injected through constructors.
- Each use case has one public `execute()` method.

## Development workflow: TDD
- **Skill:** copy the `tdd` skill as-is from `/Users/admin/Code/kilgrave_client_app` (branch `release/net10-upgrade`, `.claude/skills/tdd/SKILL.md`) into `Chess/.claude/skills/tdd/SKILL.md`, using `git show release/net10-upgrade:.claude/skills/tdd/SKILL.md > …` so the checked-out branch there isn't touched. `CLAUDE.md` will say that all feature work follows this skill.
- **Loop for each behavior:** RED (one failing test) → GREEN (the smallest code that passes) → REFACTOR (only while tests are green). Never write several tests at once. Sub-agents handle repo discovery, test runs with failure analysis, and refactor scouting.
- **Test style**, following the skill's philosophy: tests check behavior through public interfaces, meaning use case `execute()`, domain services and CLI commands, not private details.
  - Test doubles are used **only at port boundaries**: in-memory `GameSource` and `GameRepository` fakes in `tests/fakes.py`, and a scripted `PositionEngine` fake. Internal collaborators are never mocked.
  - Adapters get their own integration tests: SQLite in a temp dir, chess.com through recorded JSON fixtures (served with `respx`), and the real Stockfish inside the container (marked `slow`).
- **Commands inside Docker:**
  - Narrowest test: `docker compose run --rm dev pytest tests/<path>::<test> -q`
  - Full suite: `make test`
  - Everything: `make check`
- **Test order for each slice:** domain behavior → use case with fakes → adapter integration → CLI e2e. Example first tests for Phase 1:
  1. `mapper` turns a chess.com game JSON fixture into a domain `Game` with the correct color and result for the configured user.
  2. `SyncGames` stores all games from a fake source.
  3. Running `SyncGames` a second time adds nothing (idempotent).
  4. `SyncGames` only fetches months newer than the last sync.
  5. The chess.com client retries after a 429.
  6. `coach sync` prints a summary of the imported games.
- Small conventional commits per slice.

**Storage** (SQLite adapter, behind the repository ports). Tables:
- `games`: id, url, time_class, color, result, ratings, ECO/opening, pgn, end_time
- `move_analyses`: game_id, ply, san, fen_before, clock, eval_before, eval_after, best_move, win_pct_loss, classification, phase
- `sync_state`: archive_url, etag, last_synced
- `weaknesses`/`tags`: game or move → pattern

## Repository & delivery
- **Remote:** `https://github.com/rlimaa/chess-coach.git`. The repo is empty right now. Work happens in `/Users/admin/Documents/Chess` with `git init -b main` and `git remote add origin …`.
- **One commit per phase** on `main`, pushed once the phase is done and `make check` passes. Inside a phase, the TDD red/green/refactor steps happen in the working tree and are only committed when the whole phase is finished.
- **Commit message:** `Phase N: <title>`. The body summarizes what was delivered and ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Two separate markdown files in the repo** (both part of the Phase 0 commit):
  - `PLAN.md` is the plan itself: context, research findings, architecture, Docker, TDD workflow, the phase descriptions and verification. It has **no checkboxes or status**, so it stays clean and only changes when the plan changes.
  - `TODO.md` is the progress checklist. It is updated in each phase's commit, so the repo always shows what's done and what's next. `PLAN.md` links to it.
- During a session, Claude also tracks the current phase's steps with its task list.

## Phases
**Phase 0: Setup & skeleton** (first session)
- `git init`, then copy in the `tdd` skill.
- Add the Dockerfile, docker-compose.yml, Makefile, `.env.example`, `.gitignore` and `.dockerignore`. Use `uv` for the Python dependencies (with a lockfile).
- Add `pyproject.toml` with ruff, mypy, pytest, import-linter and pre-commit configured.
- Create the empty layer folders and add the import-linter contracts.
- Write `config.toml` and a `CLAUDE.md` that documents the architecture rules.

**Phase 1: chess.com integration**
- Domain: `Game`, `Player`, `TimeControl`, `Color`.
- Port: `GameSource`, `GameRepository`.
- Adapter: `chesscom/client.py` fetches archives serially with a User-Agent like `chesscoach/0.1 (contact: <email>)`, handles 429 with backoff and stores ETags. `mapper.py` converts API JSON into domain objects. `sqlite/game_repository.py` stores games.
- Use cases: `SyncGames` (idempotent and incremental), `GetStats`.
- CLI: `coach sync` and `coach stats`, showing rating per time control, win rate by color and opening, and results over time.

**Phase 2: Engine analysis**
- Domain: `Evaluation`, `MoveClass`, `Phase`, `MoveAnalysis`, `GameAnalysis`. `classification.py` uses the Lichess formulas: win % from centipawns, judgement by win-% loss (inaccuracy ≥5, mistake ≥10, blunder ≥15, the same thresholds Lichess uses), per-move accuracy, and game accuracy as the mean of the arithmetic and harmonic means. Phase detection counts the non-pawn pieces left, then looks at the move number.
- Ports: `GameReplayer` (PGN to plies with position and clock), `PositionEngine.evaluate(fen, depth)`, `AnalysisRepository`.
- Adapters: `PgnReplayer` (python-chess), `StockfishEngine` (one UCI process per session), `CachingEngine` backed by a SQLite `engine_cache` keyed by (FEN, depth).
- Use cases: `AnalyzeGames` (newest unanalyzed games first, each position evaluated once) and `ReviewGame`.
- CLI: `coach analyze --last N [--depth D]` with a progress bar, and `coach game <id|url>` showing accuracy and your key moments.
- Deferred: multipv (second-best lines). Add it when Phase 3 needs it to separate "only move" situations from ones with several good moves.

**Phase 3a: Game-level insights** (no engine; every stored game, split by time class)
- Opening families per color (variations merged), and how games end (timeout, resignation, checkmate…).
- Clock management from the PGN `[%clk]` annotations: how often you fall below 10% of your clock, your score in time trouble, and your share of losses on time.
- Habits: score after wins, after losses and after 2+ losses within a sitting (games ≤1 h apart), by position in a session, by time of day and by weekday (in your configured `TIMEZONE`).
- Opponents: score vs. Elo expectation by pre-game rating gap. chess.com reports ratings *after* the game, so the pre-game gap is reconstructed from the rating change.
- Rating by month.
- `find_highlights` ranks weaknesses and strengths by effect size × √games.
- `coach report [-t rapid -t blitz]` writes `reports/<date>-<time class>.md` and prints the top highlights.

**Phase 3b: Engine-based weaknesses** (needs a sample of analyzed games per time class)
- Errors by phase, blunders in time trouble, missed tactics (missed mates, unpunished blunders), and winning positions not converted. These are added to the same per-time-class report.
- The sample is built by the nightly job: `make schedule` installs a launchd agent that runs `scripts/nightly-analysis.sh` at 20:00 (sync, then 100 rapid + 100 blitz games at depth 12 on 6 threads).

**Phase 4: Coaching loop & improvement plan**
- `CLAUDE.md` tells Claude to act as coach: read the latest report, query the DB, review specific games move by move, and keep a `training_plan.md` with goals, weekly focus and drills.
- A **puzzle bank from your own mistakes** (positions where you blundered, with the best move as the answer): `coach puzzles`.
- A progress check-in each week or month compares metrics with the previous period.

**Phase 5: Web dashboard** (later)
- FastAPI over the same SQLite DB, plus a small frontend: board viewer (chessground + Stockfish WASM), eval graph, weakness charts, puzzle trainer.

## Delivery order
Phase 0, then commit and push `Phase 0: project setup & skeleton`. Then Phase 1 with TDD, then commit and push `Phase 1: chess.com integration`. Once Phase 1 is in, your real games are in SQLite and `make stats` shows your stats. Each phase commit is reviewed before the next phase starts.

For Phases 3–5, weakness rules go in `domain/services/weakness_detection.py`. Reports and puzzles are use cases that output through a `ReportWriter` port. The Phase 5 FastAPI app is just another item in `interfaces/` that calls the same use cases.

## Verification
- Phase 0: `docker compose build` succeeds, `docker compose run --rm coach --help` works, and `docker compose run --rm coach engine-check` shows the Stockfish version and a test evaluation.
- Every phase: `docker compose run --rm dev make check` passes, covering ruff, mypy --strict, lint-imports (layer contracts) and pytest.
- Portability: the build succeeds on arm64 (Apple Silicon) and amd64 (`docker buildx build --platform linux/amd64`).
- Phase 1: run `coach sync` against your username. Check the game count matches your chess.com archive and that re-running imports nothing new (ETag 304s). Unit tests use recorded JSON fixtures.
- Phase 2: run `coach analyze` on one known game. Compare its blunders and accuracy roughly against chess.com's own game review. Unit-test the win % and classification thresholds.
- Phase 3/4: produce the first report and review it together here for coaching value.
