# Gita Learning Platform

Subscription-based Bhagavad Gita learning platform for schools, built with FastAPI, PostgreSQL, MinIO-compatible media storage, and a Vue 3 frontend.

## Structure

- `backend/`: FastAPI app, SQLAlchemy models, Alembic migration, seed/import tools, tests.
- `frontend/`: Vue 3/Vite learning and admin UI.
- `deploy/`: sample systemd, Nginx, and environment files for bare-metal Ubuntu deployment.
- `backend/seed_data/bhagavad_gita_export.json`: current curriculum seed import.

## Local PostgreSQL Setup

Create a local database and user matching the default development URL, or override `DATABASE_URL`.

```sql
CREATE DATABASE gita_learning;
CREATE USER gita WITH PASSWORD 'gita';
GRANT ALL PRIVILEGES ON DATABASE gita_learning TO gita;
```

Development default:

```text
postgresql+psycopg://gita:gita@127.0.0.1:5432/gita_learning
```

## Backend Setup

```powershell
cd D:\dvm\bhagavad-gita\backend
py -3.13 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

Run migrations:

```powershell
py -3.13 -m alembic upgrade head
```

Seed the platform and imported curriculum:

```powershell
$env:ALLOW_LOCAL_SEED_CREDENTIALS="true"
py -3.13 scripts\seed.py
```

For production, set `SUPER_ADMIN_EMAIL` and `SUPER_ADMIN_PASSWORD` instead of allowing local seed credentials.

Run the backend:

```powershell
cd D:\dvm\bhagavad-gita\backend
py -3.13 -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

## Frontend Setup

```powershell
cd D:\dvm\bhagavad-gita\frontend
npm install
npm run dev
```

Build for production:

```powershell
npm run build
```

## Media Storage

The backend expects S3-compatible storage, typically MinIO for self-hosting.

Required settings:

- `MINIO_ENDPOINT`
- `MINIO_BUCKET`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MAX_UPLOAD_MB`

## Ubuntu Bare-Metal Deployment

1. Copy the project to `/var/www/gita-learning`.
2. Create a Python virtual environment in `/var/www/gita-learning/backend/.venv`.
3. Install backend requirements.
4. Build the frontend with `npm run build`.
5. Copy `deploy/env.example` to `/etc/gita-learning.env` and replace all secrets.
6. Run `alembic upgrade head`.
7. Run the seed command with production super-admin credentials.
8. Copy `deploy/gita-learning.service` to `/etc/systemd/system/gita-learning.service`.
9. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gita-learning
sudo systemctl status gita-learning
```

10. Copy `deploy/nginx-gita-learning.conf` into your Nginx sites configuration, update `server_name`, enable it, and reload Nginx.

## Verification

Backend tests:

```powershell
cd D:\dvm\bhagavad-gita\backend
py -3.13 -m pytest app/tests -v
```

Frontend build:

```powershell
cd D:\dvm\bhagavad-gita\frontend
npm run build
```
