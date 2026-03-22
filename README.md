# Flight Booking BFF (FastAPI)

Backend-for-Frontend wrapper over the legacy mock API at [https://mock-travel-api.vercel.app/docs](https://mock-travel-api.vercel.app/docs).

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Wrapper Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: `GET /health`

### Environment variables (optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `LEGACY_BASE_URL` | `https://mock-travel-api.vercel.app` | Upstream base URL |
| `HTTP_TIMEOUT_SECONDS` | `30` | HTTP timeout to legacy |
| `MAX_RETRIES` | `3` | Retry attempts (timeout, 5xx, 429) |
| `CIRCUIT_FAILURE_THRESHOLD` | `5` | Failures before opening the circuit |
| `CIRCUIT_OPEN_SECONDS` | `30` | How long the circuit stays open |
| `AIRPORT_CACHE_TTL_SECONDS` | `3600` | TTL for cached airport list (city-enriched) |
| `BOOKING_CACHE_TTL_SECONDS` | `60` | TTL for `GET /v1/bookings/{ref}` cache |

Full documentation (architecture, caching, resilience, AI workflow): see [DOCUMENTATION.md](DOCUMENTATION.md).

## Debug in Cursor / VS Code

1. Create a venv, install deps (`pip install -r requirements.txt`).
2. Install the **Python** extension if prompted.
3. **Run and Debug** → pick **FastAPI: uvicorn (reload + debug)** from `.vscode/launch.json`.

Notes:

- With `--reload`, the debugger sometimes attaches to the reloader child process; if breakpoints feel flaky, use **FastAPI: uvicorn (no reload — stable breakpoints)**.
- Optional: set breakpoints in `app/` and call `http://localhost:8000/docs` or your routes.

## Deploy on [Render](https://render.com)

Render injects **`PORT`**; the start command must bind to `0.0.0.0:$PORT` (already in `render.yaml`).

### Option A — Blueprint (`render.yaml`)

1. Push this repo to GitHub/GitLab/Bitbucket.
2. In Render: **New** → **Blueprint** → connect the repo → select `render.yaml`.
3. Adjust **service name** / plan if needed, then apply.

### Option B — Web Service (dashboard)

1. **New** → **Web Service** → connect the repo.
2. **Runtime**: Python  
3. **Build command**: `pip install -r requirements.txt`  
4. **Start command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`  
5. **Health check path**: `/health`  
6. **Environment**: add any vars from the table above (at minimum `LEGACY_BASE_URL` if you ever change upstream).

`runtime.txt` pins the Python version for Render’s build. If the dashboard shows a different version, align it with `runtime.txt` or set **PYTHON_VERSION** to match.

After deploy, open `https://<your-service>.onrender.com/docs` for Swagger.
