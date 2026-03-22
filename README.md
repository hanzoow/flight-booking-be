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

---

## Hướng dẫn deploy Render (chi tiết, tiếng Việt)

### URL Swagger của **BFF** (project này)

Sau khi deploy, tài liệu API **wrapper** của bạn là:

`https://<tên-service-trên-render>.onrender.com/docs`

Ví dụ bạn đặt tên service là `flight-booking-be` thì thường là:

`https://flight-booking-be.onrender.com/docs`

Render đôi khi thêm hậu tố nếu trùng tên (ví dụ `flight-booking-be-h4ir`) — **URL chính xác** nằm trên dashboard service → mục **URL**.

**Lưu ý:** Link dạng `...#/Airports/list_airports_api_v1_airports_get` là kiểu **Swagger của legacy** (`mock-travel-api`). App của bạn là **API khác** (path có tiền tố `/v1/`, tag thường là `airports` chữ thường). Ví dụ mở thẳng một operation trong Swagger UI có thể giống:

`https://<service>.onrender.com/docs#/airports/list_airports_v1_airports_get`

(phần sau `#` có thể hơi khác tùy phiên bản FastAPI/Swagger UI; cứ vào `/docs` rồi chọn nhóm **airports** là đủ.)

### Cách tạo Web Service trên Render (từng bước)

1. Đăng nhập [render.com](https://render.com), kết nối **GitHub/GitLab/Bitbucket** (nếu chưa).
2. **Dashboard** → **New +** → **Web Service**.
3. **Connect** repository chứa project `flight-api-wrapper` (branch `main` hoặc branch bạn dùng).
4. Điền form:
   - **Name**: ví dụ `flight-booking-be` (dùng làm phần đầu subdomain `.onrender.com`).
   - **Region**: gần bạn nhất.
   - **Branch**: branch chứa code đã push.
   - **Root directory**: để trống (nếu code ở root repo).
   - **Runtime**: **Python 3**.
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Chọn **plan** (Free hoặc trả phí).
6. Mục **Advanced** (hoặc **Health Check**):
   - **Health Check Path**: `/health`
7. **Environment** → **Add Environment Variable** (khuyến nghị):
   - `LEGACY_BASE_URL` = `https://mock-travel-api.vercel.app`
   - (Tùy chọn) `PYTHON_VERSION` = `3.12.8` — nên trùng với `runtime.txt`.
8. **Create Web Service**. Đợi lần **build + deploy** đầu tiên (vài phút).
9. Khi **Live**, mở **URL** trên dashboard:
   - Kiểm tra: `https://<service>.onrender.com/health` → `{"status":"ok"}`
   - Swagger: `https://<service>.onrender.com/docs`

### Deploy bằng Blueprint (`render.yaml`)

1. Push repo có file `render.yaml` (đã có trong project).
2. **New +** → **Blueprint** → chọn repo → Render đọc `render.yaml`.
3. **Apply** — chỉnh **service name** trong file hoặc trên UI nếu cần URL cụ thể.

### Sau khi deploy — gọi API giống local

Chỉ đổi host: ví dụ list airports:

```bash
curl -sS "https://flight-booking-be-h4ir.onrender.com/v1/airports"
```

(Thay `flight-booking-be-h4ir` bằng **URL thật** trên Render của bạn.)

### Gói Free

- Instance **sleep** khi không có traffic; request đầu sau idle có thể **chậm ~30–60s**.
- Nếu build báo lỗi Python, chỉnh **PYTHON_VERSION** / `runtime.txt` cho khớp phiên bản Render hỗ trợ.
