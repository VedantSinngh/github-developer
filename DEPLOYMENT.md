# Production Deployment Guide: Render (Backend) & Vercel (Frontend)

This repository is organized to allow seamless, decoupled deployment of the **FastAPI Backend on Render** and the **Next.js Frontend on Vercel**.

---

## 1. Backend Deployment (Render)

### Option A: Render Blueprint (Recommended — 1 Click)
1. Push your latest code to GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com/) -> **New** -> **Blueprint**.
3. Connect your GitHub repository (`VedantSinngh/github-developer`).
4. Render will automatically detect [`render.yaml`](file:///c:/Users/vedaa/OneDrive/Desktop/resume-project/github/render.yaml), create a Managed PostgreSQL Database (`candidate-eval-db`), build the API, run Alembic migrations, and deploy the FastAPI web service.

### Option B: Manual Setup on Render
1. **Database**: Create a PostgreSQL instance on Render. Copy the **Internal Database URL**.
2. **Web Service**:
   - **Environment**: Python 3.11+
   - **Build Command**: `./render_build.sh` (or `pip install -r requirements.txt && alembic upgrade head`)
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `DATABASE_URL`: Your Render PostgreSQL connection string (starts with `postgresql+asyncpg://`)
     - `JWT_SECRET`: Random 32+ character string
     - `ENCRYPTION_KEY`: Fernet key generated via `cryptography.fernet.Fernet.generate_key()`
     - `GITHUB_CLIENT_ID`: Your GitHub OAuth app client ID
     - `GITHUB_CLIENT_SECRET`: Your GitHub OAuth app client secret

---

## 2. Frontend Deployment (Vercel)

1. Go to [Vercel Dashboard](https://vercel.com/new).
2. Import your GitHub repository (`VedantSinngh/github-developer`).
3. Set the **Root Directory** to `frontend`.
4. Vercel will automatically detect **Next.js**.
5. Add the **Environment Variable**:
   - `NEXT_PUBLIC_API_URL`: `https://your-render-backend-url.onrender.com`
6. Click **Deploy**.

---

## 3. Project Structure Reference

```
.
├── Procfile                      # Render start command specification
├── requirements.txt              # Backend dependencies
├── render_build.sh               # Render build & Alembic migration script
├── render.yaml                   # Render Infrastructure-as-Code blueprint
├── main.py                       # FastAPI application entry point
├── routes.py                     # API routes & slowapi rate limits
├── models.py                     # SQLAlchemy models
├── sync_service.py               # GitHub GraphQL sync service
├── scoring_engine.py             # 5-signal scoring engine
├── alembic/                      # Database migrations
└── frontend/                     # Next.js 14 App Router project (Vercel Root)
    ├── vercel.json               # Vercel configuration
    ├── package.json              # Frontend dependencies
    └── src/                      # App router pages & ElevenLabs UI components
```
