FROM node:24-alpine AS frontend-build
WORKDIR /frontend

COPY web/package*.json ./
RUN npm ci && npm cache clean --force

COPY web/ ./

ARG VERSION
ARG BASE_PATH=""
RUN env PUBLIC_VERSION=${VERSION} PUBLIC_API_URL=${BASE_PATH} BASE_PATH=${BASE_PATH}/web npm run build

FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim AS base 

RUN apt-get update && \
    apt-get install -y ca-certificates bash libtorrent21 gcc bc locales postgresql media-types mailcap curl gzip unzip tar 7zip bzip2 unar && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
RUN locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Create a non-root user and group
RUN groupadd -g 1000 mediamanager && \
    useradd -m -u 1000 -g mediamanager mediamanager

FROM base AS dependencies
WORKDIR /app
# Ensure mediamanager owns /app
RUN chown -R mediamanager:mediamanager /app

USER mediamanager

# Set uv cache to a writable home directory and use copy mode for volume compatibility
ENV UV_CACHE_DIR=/home/mediamanager/.cache/uv \
    UV_LINK_MODE=copy

COPY --chown=mediamanager:mediamanager pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/home/mediamanager/.cache/uv,uid=1000,gid=1000 \
    uv sync --locked

FROM dependencies AS app
ARG VERSION
ARG BASE_PATH=""
LABEL author="github.com/maxdorninger"
LABEL version=${VERSION}
LABEL description="Docker image for MediaManager"

ENV PUBLIC_VERSION=${VERSION} \
    CONFIG_DIR="/app/config" \
    BASE_PATH=${BASE_PATH} \
    FRONTEND_FILES_DIR="/app/web/build"

COPY --chown=mediamanager:mediamanager --chmod=755 mediamanager-startup.sh .
COPY --chown=mediamanager:mediamanager config.example.toml .
COPY --chown=mediamanager:mediamanager media_manager ./media_manager
COPY --chown=mediamanager:mediamanager alembic ./alembic
COPY --chown=mediamanager:mediamanager alembic.ini .

HEALTHCHECK CMD curl -f http://localhost:8000${BASE_PATH}/api/v1/health || exit 1
EXPOSE 8000
CMD ["/app/mediamanager-startup.sh"]

FROM app AS production
COPY --chown=mediamanager:mediamanager --from=frontend-build /frontend/build /app/web/build
