"""
FastAPI Routes for Candidate Evaluation Platform.
Includes missing endpoints: GET /evaluations, GET /evaluations/{id}, POST /evaluations/{id}/sync (rate-limited 1/min), GET /evaluations/{id}/share/{token} (public read-only).
"""

from datetime import datetime, timezone
from decimal import Decimal
import io
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Commit,
    Evaluation,
    EvaluationStatus,
    GitHubConnection,
    PullRequest,
    Recruiter,
    RoleProfile,
    ScoreBreakdown,
)
from schemas import (
    EvaluationCreateRequest,
    EvaluationResponse,
    RecruiterLoginRequest,
    RecruiterRegisterRequest,
    RecruiterResponse,
    RoleProfileCreateRequest,
    RoleProfileResponse,
    ScoreResponse,
    TimelineItem,
    TokenResponse,
)
from scoring_engine import compute_final_score, persist_score
from sync_service import GitHubSyncService

SECRET_KEY = "DEV_SECRET_KEY_CHANGE_IN_PRODUCTION"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

# In-memory rate limiting tracker for manual sync (1 per minute per evaluation)
sync_rate_tracker: Dict[int, float] = {}

async def get_db():
    raise NotImplementedError("Database session dependency must be overridden by app.")


async def get_current_recruiter(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Recruiter:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token claims")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    res = await db.execute(select(Recruiter).where(Recruiter.email == email))
    recruiter = res.scalar_one_or_none()
    if not recruiter:
        raise HTTPException(status_code=401, detail="Recruiter not found")
    return recruiter


# Auth Endpoints with slowapi rate limits
@router.post(
    "/auth/register",
    response_model=RecruiterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new recruiter account",
)
@limiter.limit("3/minute")
async def register(request: Request, req: RecruiterRegisterRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Recruiter).where(Recruiter.email == req.email))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    recruiter = Recruiter(
        email=req.email,
        hashed_password=pwd_context.hash(req.password),
        org_name=req.org_name,
    )
    db.add(recruiter)
    await db.commit()
    await db.refresh(recruiter)
    return recruiter


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Authenticate recruiter and issue JWT token",
)
@limiter.limit("5/minute")
async def login(request: Request, req: RecruiterLoginRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Recruiter).where(Recruiter.email == req.email))
    recruiter = res.scalar_one_or_none()
    if not recruiter or not pwd_context.verify(req.password, recruiter.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token_data = {"sub": recruiter.email, "org": recruiter.org_name}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return TokenResponse(access_token=token)


@router.get("/auth/github/callback", summary="GitHub OAuth Callback")
async def github_callback(code: str, state: Optional[str] = None):
    return {"status": "success", "message": "GitHub connection authorization received", "code": code}


# Role Profiles Endpoints
@router.post(
    "/role-profiles",
    response_model=RoleProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role scoring weight profile",
)
async def create_role_profile(
    req: RoleProfileCreateRequest,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    rp = RoleProfile(**req.model_dump())
    db.add(rp)
    await db.commit()
    await db.refresh(rp)
    return rp


@router.get(
    "/role-profiles",
    response_model=List[RoleProfileResponse],
    summary="List all configured role profiles",
)
async def list_role_profiles(
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(RoleProfile))
    return res.scalars().all()


# Evaluation Endpoints
@router.post(
    "/evaluations",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a candidate evaluation",
)
async def create_evaluation(
    req: EvaluationCreateRequest,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    if req.end_date <= req.start_date:
        raise HTTPException(status_code=400, detail="end_date must be strictly after start_date")

    evaluation = Evaluation(
        recruiter_id=current_user.id,
        status=EvaluationStatus.PENDING,
        **req.model_dump(),
    )
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)
    return evaluation


@router.get(
    "/evaluations",
    response_model=List[EvaluationResponse],
    summary="List recruiter's own evaluations",
)
async def list_evaluations(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = 0,
    limit: int = 20,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Evaluation).where(Evaluation.recruiter_id == current_user.id)
    if status_filter:
        stmt = stmt.where(Evaluation.status == status_filter)
    stmt = stmt.offset(skip).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get(
    "/evaluations/{id}",
    response_model=EvaluationResponse,
    summary="Get full evaluation detail",
)
async def get_evaluation_detail(
    id: int,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Evaluation).where(Evaluation.id == id, Evaluation.recruiter_id == current_user.id)
    )
    evaluation = res.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


@router.post(
    "/evaluations/{id}/activate",
    response_model=EvaluationResponse,
    summary="Activate evaluation",
)
async def activate_evaluation(
    id: int,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Evaluation).where(Evaluation.id == id, Evaluation.recruiter_id == current_user.id)
    )
    evaluation = res.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    if evaluation.status != EvaluationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending evaluations can be activated")

    evaluation.status = EvaluationStatus.ACTIVE
    await db.commit()
    await db.refresh(evaluation)
    return evaluation


@router.post(
    "/evaluations/{id}/sync",
    summary="Manual sync trigger (Rate-limited max 1/min per evaluation)",
)
async def manual_sync_trigger(
    id: int,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    # Enforce 1 min rate limit per evaluation
    last_sync = sync_rate_tracker.get(id, 0)
    now_ts = time.time()
    if now_ts - last_sync < 60:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Manual sync for evaluation {id} is restricted to 1 call per minute.",
        )

    res = await db.execute(
        select(Evaluation).where(Evaluation.id == id, Evaluation.recruiter_id == current_user.id)
    )
    evaluation = res.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    sync_rate_tracker[id] = now_ts

    conn_res = await db.execute(
        select(GitHubConnection).where(GitHubConnection.evaluation_id == id)
    )
    conn = conn_res.scalar_one_or_none()
    token = conn.access_token if conn else "mock_token"

    sync_service = GitHubSyncService()
    log = await sync_service.sync_evaluation(db, id, token)
    return {"status": "success", "message": "Manual sync completed", "log_id": log.id}


@router.get(
    "/evaluations/{id}/timeline",
    response_model=List[TimelineItem],
    summary="Get evaluation activity timeline",
)
async def get_timeline(
    id: int,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    commits_res = await db.execute(select(Commit).where(Commit.evaluation_id == id))
    commits = commits_res.scalars().all()

    prs_res = await db.execute(select(PullRequest).where(PullRequest.evaluation_id == id))
    prs = prs_res.scalars().all()

    timeline = []
    for c in commits:
        timeline.append(
            TimelineItem(
                type="commit",
                id=c.id,
                timestamp=c.committed_at,
                author=c.author_login,
                summary=f"Commit: {c.message[:50]} (+{c.additions}/-{c.deletions})",
            )
        )
    for pr in prs:
        timeline.append(
            TimelineItem(
                type="pull_request",
                id=pr.id,
                timestamp=pr.opened_at,
                author=pr.author_login,
                summary=f"Opened PR #{pr.pr_number} (+{pr.additions}/-{pr.deletions})",
            )
        )

    timeline.sort(key=lambda x: x.timestamp)
    return timeline


@router.get(
    "/evaluations/{id}/score",
    response_model=ScoreResponse,
    summary="Get live in-progress or locked score",
)
async def get_score(
    id: int,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Evaluation).where(Evaluation.id == id, Evaluation.recruiter_id == current_user.id)
    )
    evaluation = res.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    if evaluation.status == EvaluationStatus.LOCKED:
        sb_res = await db.execute(
            select(ScoreBreakdown).where(ScoreBreakdown.evaluation_id == id)
        )
        breakdowns = sb_res.scalars().all()
        metrics = {
            b.metric_name: {
                "raw": float(b.raw_value),
                "normalized": float(b.normalized_score),
                "weight": float(b.weight),
            }
            for b in breakdowns
        }
        return ScoreResponse(
            evaluation_id=evaluation.id,
            status=evaluation.status.value,
            final_score=float(evaluation.final_score) if evaluation.final_score else 0.0,
            is_locked=True,
            metrics=metrics,
            flagged_notes=["Evaluation locked. Score breakdown retrieved from immutable ledger."],
        )

    commits_res = await db.execute(select(Commit).where(Commit.evaluation_id == id))
    commits = list(commits_res.scalars().all())

    prs_res = await db.execute(select(PullRequest).where(PullRequest.evaluation_id == id))
    prs = list(prs_res.scalars().all())

    rp_res = await db.execute(
        select(RoleProfile).where(RoleProfile.id == (evaluation.role_profile_id or 1))
    )
    role_profile = rp_res.scalar_one_or_none() or RoleProfile(
        id=1,
        name="Default",
        weight_consistency=Decimal("0.2"),
        weight_pr_quality=Decimal("0.25"),
        weight_review_cycles=Decimal("0.2"),
        weight_collaboration=Decimal("0.15"),
        weight_stability=Decimal("0.2"),
    )

    computed = compute_final_score(
        candidate_login=evaluation.github_username,
        start_date=evaluation.start_date,
        end_date=evaluation.end_date,
        commits=commits,
        commit_files=[],
        prs=prs,
        all_prs=prs,
        reviewers=[],
        comments=[],
        role_profile=role_profile,
    )

    flagged_notes = []
    if commits:
        total_dur = (evaluation.end_date - evaluation.start_date).total_seconds()
        thresh = evaluation.start_date.timestamp() + (total_dur * 0.9)
        late_commits = sum(1 for c in commits if c.committed_at.timestamp() >= thresh)
        late_pct = round((late_commits / len(commits)) * 100, 1)
        if late_pct > 60.0:
            flagged_notes.append(f"High concentration penalty: {late_pct}% of commits in final 10% window.")

    return ScoreResponse(
        evaluation_id=evaluation.id,
        status=evaluation.status.value,
        final_score=computed["final_score"],
        is_locked=False,
        metrics=computed["metrics"],
        flagged_notes=flagged_notes,
    )


@router.get(
    "/evaluations/{id}/share/{token}",
    response_model=ScoreResponse,
    summary="Public read-only score card by share token (No auth required)",
)
@limiter.limit("30/minute")
async def get_public_share_score_card(
    request: Request, id: int, token: str, db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Evaluation).where(
            Evaluation.id == id, Evaluation.share_token == token, Evaluation.status == EvaluationStatus.LOCKED
        )
    )
    evaluation = res.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(
            status_code=404,
            detail="Public share card not found or evaluation is not locked yet.",
        )

    sb_res = await db.execute(
        select(ScoreBreakdown).where(ScoreBreakdown.evaluation_id == id)
    )
    breakdowns = sb_res.scalars().all()
    metrics = {
        b.metric_name: {
            "raw": float(b.raw_value),
            "normalized": float(b.normalized_score),
            "weight": float(b.weight),
        }
        for b in breakdowns
    }

    return ScoreResponse(
        evaluation_id=evaluation.id,
        status=evaluation.status.value,
        final_score=float(evaluation.final_score) if evaluation.final_score else 0.0,
        is_locked=True,
        metrics=metrics,
        flagged_notes=["Verified immutable report card."],
    )


@router.get(
    "/evaluations/{id}/report",
    summary="Generate and download PDF report card",
)
async def generate_report(
    id: int,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Evaluation).where(Evaluation.id == id, Evaluation.recruiter_id == current_user.id)
    )
    evaluation = res.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Candidate Evaluation Report Card", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Candidate Name: {evaluation.candidate_name}", styles["Heading2"]))
    story.append(Paragraph(f"Repository: {evaluation.repo_owner}/{evaluation.repo_name}", styles["Normal"]))
    story.append(Paragraph(f"Evaluation Window: {evaluation.start_date.strftime('%Y-%m-%d')} to {evaluation.end_date.strftime('%Y-%m-%d')}", styles["Normal"]))
    story.append(Paragraph(f"Status: {evaluation.status.value.upper()}", styles["Normal"]))
    story.append(Paragraph(f"Final Score: {evaluation.final_score or 'N/A'}", styles["Heading1"]))
    story.append(Spacer(1, 18))

    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_card_eval_{id}.pdf"},
    )
