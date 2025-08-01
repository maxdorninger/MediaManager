FROM node:24-alpine AS frontend-build
WORKDIR /frontend
ARG VERSION
ARG BASE_PATH=""

COPY web/package*.json ./
RUN npm ci && npm cache clean --force

COPY web/ ./
RUN env PUBLIC_VERSION=${VERSION} PUBLIC_API_URL=${BASE_PATH}/api/v1 BASE_PATH=${BASE_PATH}/web npm run build

FROM ghcr.io/astral-sh/uv:debian-slim
ARG VERSION
ARG BASE_PATH=""
LABEL author="github.com/maxdorninger"
LABEL version=${VERSION}
LABEL description="Docker image for MediaManager"

ENV PUBLIC_VERSION=${VERSION} \
    CONFIG_DIR="/app/config"\
    BASE_PATH=${BASE_PATH}\
    FRONTEND_FILES_DIR="/app/web/build"


WORKDIR /app

RUN apt-get update && \
    apt-get install -y ca-certificates bash libtorrent21 gcc bc locales postgresql mime-support curl gzip unzip tar 7zip bzip2 unar && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
RUN locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

COPY pyproject.toml uv.lock ./
RUN uv sync --locked

COPY --chmod=755 mediamanager-startup.sh .
COPY config.example.toml .
COPY media_manager ./media_manager
COPY alembic ./alembic
COPY alembic.ini .

COPY --from=frontend-build /frontend/build /app/web/build

HEALTHCHECK CMD curl -f http://localhost:8000${BASE_PATH}/api/v1/health || exit 1
EXPOSE 8000
CMD ["/app/mediamanager-startup.sh"]
