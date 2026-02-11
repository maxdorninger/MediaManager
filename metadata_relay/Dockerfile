FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim
ARG VERSION
LABEL version=${VERSION}

ENV BASE_PATH=""

RUN apt-get update && apt-get install -y ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 mediamanager && \
    useradd -m -u 1000 -g mediamanager mediamanager

WORKDIR /app
RUN chown -R mediamanager:mediamanager /app

ENV UV_CACHE_DIR=/home/mediamanager/.cache/uv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

COPY --chown=mediamanager:mediamanager pyproject.toml uv.lock ./

USER mediamanager
RUN --mount=type=cache,target=/home/mediamanager/.cache/uv,uid=1000,gid=1000 \
    uv sync --frozen --no-install-project --no-dev

COPY --chown=mediamanager:mediamanager . .

RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uv", "run", "fastapi", "run", "/app/main.py", "--port", "8000", "--proxy-headers"]