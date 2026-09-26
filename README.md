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
make web                    # dashboard on http://localhost:8000
make sync                   # import new games from chess.com
make analyze                # Stockfish analysis of recent games
make report                 # rapid + blitz coaching reports in reports/
make puzzles                # puzzles from your own mistakes (TC=blitz to filter)
make progress               # last 30 days vs the 30 before (TC=rapid|blitz)
make schedule               # scheduler container: nightly sync + analysis at 20:00
docker compose run --rm coach --help
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

## Credits
- Stockfish (GPLv3): https://github.com/official-stockfish/Stockfish
- Board: chessground (GPLv3). Pieces: Maestro by sadsnake1, CC BY-NC-SA 4.0, served from the lichess.org repository. Non-commercial use only.
