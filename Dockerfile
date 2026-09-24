# syntax=docker/dockerfile:1.7
ARG PYTHON_VERSION=3.13
ARG STOCKFISH_VERSION=sf_19
ARG UV_VERSION=0.8

# --- Stage 1: build Stockfish from source for the target CPU -----------------
FROM debian:bookworm-slim AS stockfish-builder
ARG STOCKFISH_VERSION
ARG TARGETARCH
# Leave empty to pick from TARGETARCH; override for older CPUs, e.g. SF_ARCH=x86-64-sse41-popcnt.
ARG SF_ARCH=""
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential git ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch "${STOCKFISH_VERSION}" \
      https://github.com/official-stockfish/Stockfish.git /stockfish
WORKDIR /stockfish/src
RUN arch="${SF_ARCH}"; \
    if [ -z "$arch" ]; then \
      case "${TARGETARCH}" in \
        arm64) arch=armv8 ;; \
        amd64) arch=x86-64-avx2 ;; \
        *)     arch=general-64 ;; \
      esac; \
    fi; \
    make -j"$(nproc)" build ARCH="$arch" \
 && strip stockfish \
 && install -m 0755 stockfish /usr/local/bin/stockfish

# --- Stage 2: shared Python base -------------------------------------------
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM python:${PYTHON_VERSION}-slim AS base
COPY --from=uv /uv /uvx /bin/
COPY --from=stockfish-builder /usr/local/bin/stockfish /usr/local/bin/stockfish
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"
RUN useradd --create-home --uid 1000 coach
WORKDIR /app

# --- Stage 3: dev (tests, lint, type checks) --------------------------------
FROM base AS dev
RUN apt-get update \
 && apt-get install -y --no-install-recommends make git \
 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project
COPY . .
RUN uv sync --frozen
ENV IN_CONTAINER=1
USER coach
CMD ["make", "check"]

# --- Stage 4: runtime (the `coach` CLI) -------------------------------------
FROM base AS runtime
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable \
 && mkdir -p /app/data /app/reports \
 && chown coach:coach /app/data /app/reports
USER coach
ENTRYPOINT ["coach"]
CMD ["--help"]
