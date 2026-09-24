# Host targets wrap Docker; inside the dev container (IN_CONTAINER=1) the
# quality targets run the tools directly.
.DEFAULT_GOAL := help
COACH := docker compose run --rm coach

.PHONY: help build lock shell engine-check sync analyze stats report puzzles progress web schedule unschedule \
        check lint format typecheck arch test test-fast

help: ## Show available targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-14s %s\n", $$1, $$2}'

build: ## Build the Docker images
	docker compose build

lock: ## Refresh uv.lock (inside Docker, no local uv needed)
	docker run --rm -v "$(CURDIR)":/app -w /app ghcr.io/astral-sh/uv:0.8-python3.13-bookworm-slim uv lock

shell: ## Open a shell in the dev container
	docker compose run --rm dev bash

engine-check: ## Verify Stockfish runs inside the container
	$(COACH) engine-check

sync: ## Import games from chess.com
	$(COACH) sync

analyze: ## Analyze recent games with Stockfish
	$(COACH) analyze

stats: ## Show rating and results stats
	$(COACH) stats

report: ## Generate the coaching reports (rapid + blitz)
	$(COACH) report

puzzles: ## Solve puzzles from your own mistakes (TC=blitz to filter)
	$(COACH) puzzles $(if $(TC),--time-class $(TC))

progress: ## Last 30 days vs the 30 before (TC=blitz by default)
	$(COACH) progress --time-class $(or $(TC),blitz)

web: ## Dashboard on http://localhost:8000
	docker compose up web

schedule: ## Run sync + analysis nightly on macOS (HOUR=20 by default)
	./scripts/schedule-nightly.sh install

unschedule: ## Remove the nightly job
	./scripts/schedule-nightly.sh uninstall

ifeq ($(IN_CONTAINER),1)
check: lint typecheck arch test ## Run every quality gate

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

typecheck:
	mypy

arch:
	lint-imports

test:
	pytest --cov --cov-report=term-missing:skip-covered

test-fast:
	pytest -m "not slow"
else
check lint format typecheck arch test test-fast: ## Quality gates (run in the dev container)
	docker compose run --rm dev make $@
endif
