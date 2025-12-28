FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim
ARG VERSION
LABEL version=${VERSION}

ENV BASE_PATH=""

RUN apt-get update && apt-get install -y ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd -g 1000 mediamanager && \
    useradd -m -u 1000 -g mediamanager mediamanager

WORKDIR /app
# Ensure mediamanager owns the app directory
RUN chown -R mediamanager:mediamanager /app

USER mediamanager

# Set uv cache to a writable home directory and use copy mode for volume compatibility
ENV UV_CACHE_DIR=/home/mediamanager/.cache/uv \
    UV_LINK_MODE=copy

COPY --chown=mediamanager:mediamanager . .
RUN --mount=type=cache,target=/home/mediamanager/.cache/uv,uid=1000,gid=1000 \
    uv sync --locked

EXPOSE 8000
CMD ["uv", "run", "fastapi", "run", "/app/main.py"]