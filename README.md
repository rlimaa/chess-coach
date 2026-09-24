# Chess Coach

A personal chess coach. It imports your games from the chess.com public API, analyzes every move
with Stockfish, finds recurring weaknesses and produces coaching reports. You can then discuss those
reports with Claude.

- Plan and architecture: [PLAN.md](PLAN.md)
- Progress: [TODO.md](TODO.md)

## Requirements
Only [Docker](https://docs.docker.com/get-docker/) (with Compose v2). Python and Stockfish run
inside the image, and Stockfish is compiled from source for your CPU (arm64 or amd64).

## Setup
```bash
git clone https://github.com/rlimaa/chess-coach.git
cd chess-coach
cp .env.example .env        # set CHESSCOM_USERNAME and CONTACT_EMAIL
make build                  # first build compiles Stockfish (a few minutes)
make engine-check           # confirms the engine works
```

## Usage
```bash
docker compose run --rm coach --help
make sync                   # import games (Phase 1)
make stats                  # rating & results overview (Phase 1)
```

## Configuration
Precedence: environment variables (`.env`) > `config.toml` > defaults.
Nested engine settings use a double underscore, e.g. `ENGINE__THREADS=4`.

On older x86 CPUs without AVX2, build with `docker compose build --build-arg SF_ARCH=x86-64-sse41-popcnt`.

## Development
```bash
make check                  # ruff, mypy --strict, import-linter, pytest (in Docker)
make test-fast              # skip tests that need the real engine
make shell                  # shell inside the dev container
```
Development is test-driven (see `.claude/skills/tdd/SKILL.md`), and the Clean Architecture layer
rules are enforced by `lint-imports`.

Stockfish is GPLv3: https://github.com/official-stockfish/Stockfish
