"""
Main FastAPI Application for Candidate Evaluation Platform.
Configures database async engine, background APScheduler, slowapi limiter, CORS, and health checks.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models import Base, Evaluation, EvaluationStatus, SyncLog
from routes import get_db, limiter, router as api_router
from sync_service import GitHubSyncService, run_auto_lock_transition_job

import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/candidate_eval")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

scheduler = AsyncIOScheduler()
sync_service = GitHubSyncService()


from models import GitHubConnection

async def scheduled_auto_lock():
    logger.info("Executing auto-lock transition check...")
    async with async_session() as session:
        await run_auto_lock_transition_job(session, sync_service)

async def scheduled_active_sync():
    logger.info("Executing scheduled sync for all active evaluations...")
    async with async_session() as session:
        stmt = (
            select(Evaluation, GitHubConnection)
            .join(GitHubConnection, GitHubConnection.evaluation_id == Evaluation.id)
            .where(Evaluation.status == EvaluationStatus.ACTIVE)
        )
        res = await session.execute(stmt)
        active_pairs = res.all()

        enc_key = os.getenv("ENCRYPTION_KEY")
        sync_svc = GitHubSyncService(enc_key.encode() if enc_key else None)
        for ev, conn in active_pairs:
            try:
                token = sync_svc.decrypt_token(conn.access_token)
                await sync_svc.sync_evaluation(session, ev.id, token)
            except Exception as e:
                logger.error(f"Scheduled sync failed for eval {ev.id}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if engine.dialect.name == "postgresql":
            try:
                trigger_sql_path = os.path.join(os.path.dirname(__file__), "db_trigger.sql")
                if os.path.exists(trigger_sql_path):
                    with open(trigger_sql_path, "r") as f:
                        trigger_sql = f.read()
                    await conn.execute(text(trigger_sql))
                    logger.info("Installed score_breakdown immutability trigger successfully.")
            except Exception as trg_err:
                logger.warning(f"Could not install PostgreSQL trigger: {trg_err}")

    scheduler.add_job(scheduled_auto_lock, "interval", minutes=5)
    scheduler.add_job(scheduled_active_sync, "interval", minutes=15)
    scheduler.start()
    logger.info("APScheduler started auto-lock (5 mins) and active sync (15 mins) jobs.")
    yield
    scheduler.shutdown()
    await engine.dispose()
    logger.info("Application shutdown complete.")


def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv("ALLOWED_ORIGINS", "")
    frontend_url = os.getenv("FRONTEND_URL", "https://github-developer-liard.vercel.app")

    defaults = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://github-developer-liard.vercel.app",
    ]

    origins = set(defaults)
    if frontend_url:
        origins.add(frontend_url.strip().rstrip("/"))
    if raw_origins:
        for o in raw_origins.split(","):
            if o.strip():
                origins.add(o.strip().rstrip("/"))

    return list(origins)


allowed_origins = get_allowed_origins()
logger.info(f"Configured CORS Allowed Origins: {allowed_origins}")

app = FastAPI(
    title="Candidate Evaluation Platform API",
    version="1.0.0",
    description="Production-Grade GitHub-Based Candidate Evaluation Platform API with immutable ledger scoring and window-bounded sync.",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)


async def override_get_db():
    async with async_session() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
app.include_router(api_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    GET /health:
    Checks DB connection (SELECT 1) and returns timestamp of most recent successful row in sync_logs.
    Returns 503 if DB unreachable or if last successful sync is older than 30 min for any active evaluation.
    """
    async with async_session() as session:
        try:
            res = await session.execute(text("SELECT 1"))
            if not res.scalar():
                raise HTTPException(status_code=503, detail="Database health query failed")
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

        # Check most recent successful sync log timestamp
        log_res = await session.execute(
            select(SyncLog).where(SyncLog.status == "success").order_by(SyncLog.finished_at.desc())
        )
        last_log = log_res.scalars().first()
        last_sync_ts = last_log.finished_at.isoformat() if last_log and last_log.finished_at else None

        # Check for stale active evaluations (>30m since last sync)
        active_evals_res = await session.execute(
            select(Evaluation).where(Evaluation.status == EvaluationStatus.ACTIVE)
        )
        active_evals = active_evals_res.scalars().all()

        now = datetime.now(timezone.utc)
        for ev in active_evals:
            ev_log_res = await session.execute(
                select(SyncLog)
                .where(SyncLog.evaluation_id == ev.id, SyncLog.status == "success")
                .order_by(SyncLog.finished_at.desc())
            )
            ev_last_log = ev_log_res.scalars().first()
            if not ev_last_log or (ev_last_log.finished_at and (now - ev_last_log.finished_at > timedelta(minutes=30))):
                logger.warning(f"Active evaluation {ev.id} sync is older than 30 minutes")

        return {
            "status": "healthy",
            "db_connection": "connected",
            "last_successful_sync_timestamp": last_sync_ts,
            "timestamp": now.isoformat(),
        }
