---
description: >-
  This section is for those who want to contribute to Media Manager or
  understand its internals.
---

# Developer Guide

## Source Code directory structure﻿

* `media_manager/`: Backend FastAPI application
* `web/`: Frontend SvelteKit application
* `docs/`: Documentation (GitBook)
* `metadata_relay/`: Metadata relay service, also FastAPI

## Special Dev Configuration﻿

### Environment Variables﻿

MediaManager uses various environment variables for configuration. In the Docker development setup (`docker-compose.dev.yaml`), most of these are automatically configured for you.

#### Backend Variables﻿

* `BASE_PATH`\
  Base path for the app (for subdirectory deployments).
* `PUBLIC_VERSION`\
  Version string displayed in `/api/v1/health`.
* `FRONTEND_FILES_DIR`\
  Directory for built frontend files (e.g. `/app/web/build` in Docker).
* `MEDIAMANAGER_MISC__DEVELOPMENT`\
  When set to `TRUE`, enables FastAPI hot-reloading in Docker.

#### Frontend Variables﻿

* `PUBLIC_API_URL`\
  API URL for backend communication (auto-configured via Vite proxy in Docker).
* `PUBLIC_VERSION`\
  Version string displayed in the frontend UI.
* `BASE_PATH`\
  Base path for frontend routing (matches backend `BASE_PATH`).

#### Docker Development Variables﻿

* `DISABLE_FRONTEND_MOUNT`\
  When `TRUE`, disables mounting built frontend files (allows separate frontend container).

{% hint style="info" %}
This is automatically set in `docker-compose.dev.yaml` to enable the separate frontend development container
{% endhint %}

#### Configuration Files﻿

* Backend: `res/config/config.toml` (created from `config.dev.toml`)
* Frontend: `web/.env` (created from `.env.example`)

## Contributing﻿

* Consider opening an issue to discuss changes before starting work

## Setting up the Development Environment﻿

I use IntellijIdea with the Pycharm and Webstorm plugins to develop this, but this guide should also work with VSCode. Normally I'd recommend Intellij, but unfortunately only Intellij Ultimate has support for FastAPI and some other features.

### Recommended VSCode Plugins﻿

* Python
* Svelte for VSCode

### Recommended Intellij/Pycharm Plugins﻿

* Python
* Svelte
* Pydantic
* Ruff
* VirtualKit

### Recommended Development Workflow﻿

The recommended way to develop MediaManager is using the fully Dockerized setup with `docker-compose.dev.yaml`. This ensures you're working in the same environment as production and makes it easy for new contributors to get started without installing Python, Node.js, or other dependencies locally.

The development environment includes:

* Backend (FastAPI) with automatic hot-reloading for Python code changes
* Frontend (SvelteKit/Vite) with Hot Module Replacement (HMR) for instant updates
* Database (PostgreSQL) pre-configured and ready to use

#### What supports hot reloading and what does not﻿

* Python code changes (.py files), Frontend code changes (.svelte, .ts, .css) and configuration changes (config.toml) reload automatically.
* Changing the backend dependencies (pyproject.toml) requires rebuilding: `docker compose -f docker-compose.dev.yaml build mediamanager`
* Changing the frontend dependencies (package.json) requires restarting the frontend container: `docker compose -f docker-compose.dev.yaml restart frontend`
* Database migrations: Automatically run on backend container startup

This approach eliminates the need for container restarts during normal development and provides the best developer experience with instant feedback for code changes.

#### How the Frontend Connects to the Backend﻿

In the Docker development setup, the frontend and backend communicate through Vite's proxy configuration:

* Frontend runs on: `http://localhost:5173` (exposed from Docker)
* Backend runs on: `http://mediamanager:8000` (Docker internal network)
* Vite proxy: Automatically forwards all `/api/*` requests from frontend to backend

This means when your browser makes a request to `http://localhost:5173/api/v1/tv/shows`, Vite automatically proxies it to `http://mediamanager:8000/api/v1/tv/shows`. The `PUBLIC_API_URL` environment variable is set to use this proxy, so you don't need to configure anything manually.

### Setting up the full development environment with Docker (Recommended)﻿

This is the easiest and recommended way to get started. Everything runs in Docker with hot-reloading enabled.

{% stepper %}
{% step %}
### Prepare config files

Create config directory (only needed on first run) and copy example config files:

```bash
mkdir -p res/config # Only needed on first run
cp config.dev.toml res/config/config.toml
cp web/.env.example web/.env
```
{% endstep %}

{% step %}
### Start all services

Recommended: Use make commands for easy development

```bash
# Recommended: Use make commands for easy development
make up
```

Alternative: Use docker compose directly (if make is not available)

```bash
docker compose -f docker-compose.dev.yaml up
```
{% endstep %}

{% step %}
### Access the application

* Frontend (with HMR): http://localhost:5173
* Backend API: http://localhost:8000
* Database: localhost:5432

The default user email is `admin@example.com` and password is `admin`, these are printed out in the logs accessible with `make logs`.

Now you can edit code and see changes instantly:

* Edit Python files → Backend auto-reloads
* Edit Svelte/TypeScript files → Frontend HMR updates in browser
* Edit config.toml → Changes apply immediately
{% endstep %}
{% endstepper %}

{% hint style="info" %}
Run `make help` to see all available development commands including `make down`, `make logs`, `make app` (shell into backend), and more.
{% endhint %}

## Setting up the backend development environment (Local)

### Clone & prerequisites

1. Clone the repository
2. cd into repo root
3. Install `uv`: https://docs.astral.sh/uv/getting-started/installation/
4. Verify installation:

```bash
uv --version
```

### Install Python with uv

```bash
uv python install 3.13
```

### Create virtual environment

```bash
uv venv --python 3.13
```

### Install dependencies

```bash
uv sync
```

### Run database migrations

```bash
uv run alembic upgrade head
```

### Run the backend (development mode)

```bash
uv run fastapi run media_manager/main.py --reload --port 8000
```

### Formatting & linting

* Format code:

```bash
ruff format .
```

* Lint code:

```bash
ruff check .
```

## Setting up the frontend development environment (Local, Optional)

Using the Docker setup above is recommended. This section is for those who prefer to run the frontend locally outside of Docker.

{% stepper %}
{% step %}
### Clone & change dir

1. Clone the repository
2. cd into repo root
3. cd into `web` directory
{% endstep %}

{% step %}
### Install Node.js (example using nvm-windows)

I used nvm-windows:

```powershell
nvm install 24.1.0
nvm use 24.1.0
```

If using PowerShell you may need:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
{% endstep %}

{% step %}
### Create .env for frontend

```bash
cp .env.example .env
```

Update `PUBLIC_API_URL` if your backend is not at `http://localhost:8000`
{% endstep %}

{% step %}
### Install dependencies and run dev server

```bash
npm install
npm run dev
```
{% endstep %}

{% step %}
### Format & lint

* Format:

```bash
npm run format
```

* Lint:

```bash
npm run lint
```
{% endstep %}
{% endstepper %}

{% hint style="info" %}
If running frontend locally, make sure to add `http://localhost:5173` to the `cors_urls` in your backend config file.
{% endhint %}

## Troubleshooting﻿

### Common Docker Development Issues﻿

<details>

<summary>Port already in use errors</summary>

* Check if ports 5173, 8000, or 5432 are already in use:
  * macOS/Linux: `lsof -i :5173`
  * Windows: `netstat -ano | findstr :5173`
* Stop conflicting services or change ports in `docker-compose.dev.yaml`

</details>

<details>

<summary>Container not showing code changes</summary>

* Verify volume mounts are correct in `docker-compose.dev.yaml`
* For backend: Ensure `./media_manager:/app/media_manager` is mounted
* For frontend: Ensure `./web:/app` is mounted
* On Windows: Check that file watching is enabled in Docker Desktop settings

</details>

<details>

<summary>Frontend changes not updating</summary>

* Check that the frontend container is running: `make ps` or `docker compose -f docker-compose.dev.yaml ps`
* Verify Vite's file watching is working (should see HMR updates in browser console)
* Try restarting the frontend container:

```bash
docker compose -f docker-compose.dev.yaml restart frontend
```

</details>

<details>

<summary>Backend changes not reloading</summary>

* Verify `MEDIAMANAGER_MISC__DEVELOPMENT=TRUE` is set in `docker-compose.dev.yaml`
* Check backend logs:

```bash
make logs ARGS="--follow mediamanager"
# or
docker compose -f docker-compose.dev.yaml logs -f mediamanager
```

* If dependencies changed, rebuild:

```bash
docker compose -f docker-compose.dev.yaml build mediamanager
```

</details>

<details>

<summary>Database migration issues</summary>

* Migrations run automatically on container startup
* To run manually:

```bash
make app
uv run alembic upgrade head
```

* To create new migration:

```bash
make app
uv run alembic revision --autogenerate -m "description"
```

</details>

<details>

<summary>Viewing logs</summary>

* All services: `make logs`
* Follow logs in real-time: `make logs ARGS="--follow"`
* Specific service: `make logs ARGS="mediamanager --follow"`

</details>

<details>

<summary>Interactive debugging (shell into containers)</summary>

* Shell into backend:

```bash
make app
# or
docker compose -f docker-compose.dev.yaml exec -it mediamanager bash
```

* Shell into frontend:

```bash
make frontend
# or
docker compose -f docker-compose.dev.yaml exec -it frontend sh
```

* Once inside, you can run commands like `uv run alembic upgrade head`, `npm install`, etc.

</details>

<details>

<summary>Volume permission issues (Linux)</summary>

* Docker containers may create files as root, causing permission issues, which can make the login page fail to show up.

Solution:

```bash
sudo chown -R $USER:$USER res/
```

* Alternatively: Run containers with your user ID or use Docker's `user:` directive (may fail in some setups).

</details>

<details>

<summary>Complete reset</summary>

If all else fails, you can completely reset your development environment:

```bash
make down
docker compose -f docker-compose.dev.yaml down -v  # Remove volumes
docker compose -f docker-compose.dev.yaml build --no-cache  # Rebuild without cache
make up
```

</details>

## Tech Stack﻿

### Backend﻿

* Python
* FastAPI
* SQLAlchemy
* Pydantic and Pydantic-Settings
* Alembic

### Frontend﻿

* TypeScript
* SvelteKit
* Tailwind CSS
* shadcn-svelte
* openapi-ts
* openapi-fetch

### CI/CD﻿

* GitHub Actions
