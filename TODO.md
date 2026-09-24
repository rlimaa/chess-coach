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
- [ ] Domain: Evaluation, WinProbability, MoveClass, classification + phase detection + accuracy
- [ ] Port: PositionEngine; Stockfish adapter with FEN cache
- [ ] AnalysisRepository (SQLite)
- [ ] Use case AnalyzeGames + CLI `coach analyze --last N`, `coach game <id>`

## Phase 3 — Weakness detection & reports
- [ ] Rules: openings, phase errors, time trouble, missed tactics, failed conversions
- [ ] Use cases DetectWeaknesses, GenerateReport + Markdown ReportWriter
- [ ] CLI `coach report`

## Phase 4 — Coaching loop
- [ ] training_plan.md workflow in CLAUDE.md
- [ ] BuildPuzzles from own mistakes + CLI `coach puzzles`
- [ ] Period-over-period progress comparison

## Phase 5 — Web dashboard
- [ ] FastAPI interface reusing use cases + `web` compose service
- [ ] Board viewer (chessground + Stockfish WASM), eval graph, weakness charts, puzzle trainer
