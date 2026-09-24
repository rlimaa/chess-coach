# Chess Coach — Roadmap

## Phase 0 — Project setup & skeleton
- [x] git init, remote, .gitignore/.dockerignore, .env.example
- [x] Copy tdd skill into .claude/skills/tdd
- [x] pyproject.toml + uv.lock (python-chess, httpx, typer, rich, pydantic-settings; dev: pytest, respx, ruff, mypy, import-linter, pre-commit)
- [x] Clean Architecture folder skeleton + import-linter contracts
- [x] Dockerfile (Stockfish build stage, dev & runtime targets), docker-compose.yml, Makefile
- [x] config.py (env > config.toml > defaults) + `coach --help` / `coach engine-check`
- [x] PLAN.md (plan, no checklist) + TODO.md (this checklist)
- [x] CLAUDE.md (coach role, architecture rules, TDD workflow; points to PLAN.md/TODO.md) + README (setup via Docker)

## Phase 1 — chess.com integration
- [x] Domain: Game, Player, TimeControl, Color, Result
- [x] Ports: GameSource, GameRepository
- [x] chess.com client (User-Agent, serial, 429 backoff, ETag) + mapper
- [x] SQLite GameRepository + schema/migrations
- [x] Use cases: SyncGames (incremental, idempotent), GetStats
- [x] CLI: `coach sync`, `coach stats`

## Phase 2 — Engine analysis
- [x] Domain: Evaluation, WinProbability, MoveClass, classification + phase detection + accuracy
- [x] Port: PositionEngine; Stockfish adapter with FEN cache
- [x] AnalysisRepository (SQLite)
- [x] Use case AnalyzeGames + CLI `coach analyze --last N`, `coach game <id>`

## Phase 3a — Game-level insights (per time class)
- [x] Opening families by color, how games end
- [x] Clock management / time trouble from PGN clocks
- [x] Habits: streaks, session length, time of day, weekday (TIMEZONE setting)
- [x] Opponent strength vs. Elo expectation (pre-game gap), rating by month
- [x] Ranked highlights + Markdown ReportWriter + `coach report`
- [x] Nightly analysis job (`make schedule`, launchd)

## Phase 3b — Engine-based weaknesses
- [ ] Build analyzed sample (nightly job: 100 rapid + 100 blitz per night), then review the first engine findings
- [x] Rules: errors by phase, blunders in time trouble, missed mates, unpunished blunders, conversion
- [x] Engine highlights + report section (shown once ≥20 games of a time class are analyzed)

## Phase 4 — Coaching loop
- [x] Coaching workflow + training plan in CLAUDE.md (`coaching/`, gitignored)
- [x] Puzzles from own mistakes with spaced repetition + `coach puzzles` (interactive / `--list`)
- [x] Period-over-period progress comparison (`coach progress`)
- [ ] First weekly check-in once the nightly analysis has built a sample

## Phase 5 — Web dashboard
- [ ] FastAPI interface reusing use cases + `web` compose service
- [ ] Board viewer (chessground + Stockfish WASM), eval graph, weakness charts, puzzle trainer
