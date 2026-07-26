# Candidate Evaluation Platform — Root Architecture

This repository is organized into a clean, decoupled full-stack architecture:

- **Root Directory (`/`)**: Backend service (FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL triggers, APScheduler, ReportLab PDF generator) configured for 1-click deployment on **Render**.
- **Frontend Directory (`/frontend`)**: Next.js 14 App Router application configured for deployment on **Vercel**.

## Architecture & File Mapping

```
.
├── Procfile                      # Render start command (uvicorn main:app)
├── render.yaml                   # Render Infrastructure-as-Code Blueprint
├── render_build.sh               # Render build & migration script
├── requirements.txt              # Backend dependencies
├── alembic.ini                   # Alembic database migration config
├── alembic/                      # Database migrations (0001_initial, 0002_add_share_token)
├── main.py                       # FastAPI entry point & health check
├── routes.py                     # API routes & rate limiters
├── models.py                     # SQLAlchemy 2.0 models & constraints
├── sync_service.py               # GitHub GraphQL sync service
├── scoring_engine.py             # Pure 5-signal scoring engine
├── db_trigger.sql                # Immutability DB trigger
├── docker-compose.yml            # Local Docker orchestrator
└── frontend/                     # Next.js 14 Frontend App (Vercel Root)
    ├── vercel.json               # Vercel configuration
    ├── package.json              # Frontend dependencies
    └── src/                      # ElevenLabs UI pages & components
```

## Deployment Setup

### 1. Render (Backend API)
- Connect GitHub repo (`VedantSinngh/github-developer`) to **Render Blueprint**.
- Render reads `render.yaml`, provisions a PostgreSQL database, executes `./render_build.sh`, and starts Uvicorn.

### 2. Vercel (Frontend App)
- Connect GitHub repo (`VedantSinngh/github-developer`) to **Vercel**.
- Set **Root Directory** to `frontend`.
- Set Environment Variable `NEXT_PUBLIC_API_URL` to your Render API domain.
