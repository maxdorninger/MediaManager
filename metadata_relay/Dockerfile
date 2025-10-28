FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim
ARG VERSION
LABEL version=${VERSION}

ENV BASE_PATH=""

RUN apt-get update && apt-get install -y ca-certificates


WORKDIR /app
COPY . .
RUN uv sync --locked
EXPOSE 8000
CMD ["uv", "run", "fastapi", "run", "/app/main.py"]
