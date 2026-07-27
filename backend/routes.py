"""
FastAPI Routes for Candidate Evaluation Platform.
Includes missing endpoints: GET /evaluations, GET /evaluations/{id}, POST /evaluations/{id}/sync (rate-limited 1/min), GET /evaluations/{id}/share/{token} (public read-only).
"""

from datetime import datetime, timezone
from decimal import Decimal
import io
import time
from typing import Dict, List, Optional
import os
import httpx
from cryptography.fernet import Fernet
import csv

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status, BackgroundTasks, File, UploadFile
from fastapi.responses import StreamingResponse, RedirectResponse
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
    Candidate,
    CandidateStatus,
    RepoTemplate,
    Cohort,
    CohortCandidate,
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
    CandidateCreateRequest,
    CandidateResponse,
    CohortCreateRequest,
    CohortResponse,
    RepoTemplateCreateRequest,
    RepoTemplateResponse,
)
from scoring_engine import compute_final_score, persist_score
from sync_service import GitHubSyncService

import bcrypt

SECRET_KEY = os.getenv("JWT_SECRET", "DEV_SECRET_KEY_CHANGE_IN_PRODUCTION")
ALGORITHM = "HS256"
security = HTTPBearer()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

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
@limiter.limit("10/minute")
async def register(request: Request, req: RecruiterRegisterRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Recruiter).where(Recruiter.email == req.email))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    recruiter = Recruiter(
        email=req.email,
        hashed_password=hash_password(req.password),
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
@limiter.limit("20/minute")
async def login(request: Request, req: RecruiterLoginRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Recruiter).where(Recruiter.email == req.email))
    recruiter = res.scalar_one_or_none()
    if not recruiter or not verify_password(req.password, recruiter.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token_data = {"sub": recruiter.email, "org": recruiter.org_name}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return TokenResponse(access_token=token)


@router.get("/auth/github/callback", summary="GitHub OAuth Callback")
async def github_callback(code: str, state: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    if not state:
        raise HTTPException(status_code=400, detail="Missing state parameter")
    
    try:
        evaluation_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state parameter, must be evaluation_id")
        
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="GitHub OAuth credentials not configured")
        
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "state": state
            },
            headers={"Accept": "application/json"}
        )
        data = response.json()
        
    if "error" in data:
        raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {data.get('error_description')}")
        
    access_token = data.get("access_token")
    scope = data.get("scope")
    
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to retrieve access token")
        
    enc_key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    cipher = Fernet(enc_key.encode())
    encrypted_token = cipher.encrypt(access_token.encode()).decode()
    
    stmt = select(GitHubConnection).where(GitHubConnection.evaluation_id == evaluation_id)
    res = await db.execute(stmt)
    conn = res.scalar_one_or_none()
    
    if conn:
        conn.access_token = encrypted_token
        conn.scope = scope
        conn.connected_at = datetime.now(timezone.utc)
    else:
        conn = GitHubConnection(
            evaluation_id=evaluation_id,
            access_token=encrypted_token,
            scope=scope
        )
        db.add(conn)
        
    await db.commit()
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(url=f"{frontend_url}/dashboard?github_connected=true")


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


# Candidate Endpoints
@router.post(
    "/candidates/bulk-upload",
    response_model=List[CandidateResponse],
    summary="Bulk upload candidates via CSV",
)
async def bulk_upload_candidates(
    file: UploadFile = File(...),
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    decoded = content.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(decoded))
    
    candidates = []
    async with httpx.AsyncClient() as client:
        for row in csv_reader:
            username = row.get("github_username", "").strip()
            if not username:
                continue
            
            # Validate GitHub username
            resp = await client.get(f"https://api.github.com/users/{username}")
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid GitHub username: {username}"
                )
            
            # Check if exists
            res = await db.execute(select(Candidate).where(Candidate.email == row.get("email")))
            if res.scalar_one_or_none():
                continue
            
            cand = Candidate(
                name=row.get("name", ""),
                email=row.get("email", ""),
                github_username=username,
            )
            db.add(cand)
            candidates.append(cand)
    
    if candidates:
        await db.commit()
        for c in candidates:
            await db.refresh(c)
            
    return candidates


# Cohort Endpoints
@router.post(
    "/cohorts",
    response_model=CohortResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new cohort",
)
async def create_cohort(
    req: CohortCreateRequest,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    cohort = Cohort(
        name=req.name,
        role_level=req.role_level,
        tech_stack=req.tech_stack,
        start_date=req.start_date,
        end_date=req.end_date,
        created_by=current_user.id,
        role_profile_id=req.role_profile_id,
        repo_template_id=req.repo_template_id,
    )
    db.add(cohort)
    await db.commit()
    await db.refresh(cohort)
    
    for c_id in req.candidate_ids:
        cc = CohortCandidate(cohort_id=cohort.id, candidate_id=c_id)
        db.add(cc)
        
    await db.commit()
    await db.refresh(cohort)
    return cohort


async def _run_cohort_start_background(cohort_id: int, current_user_id: int):
    # Fork repos and start evaluations
    from main import async_session
    async with async_session() as session:
        # Fetch cohort, template, and candidates
        res = await session.execute(select(Cohort).where(Cohort.id == cohort_id))
        cohort = res.scalar_one_or_none()
        if not cohort or not cohort.repo_template_id:
            return
            
        tpl_res = await session.execute(select(RepoTemplate).where(RepoTemplate.id == cohort.repo_template_id))
        template = tpl_res.scalar_one_or_none()
        if not template:
            return
        
        cc_res = await session.execute(select(CohortCandidate).where(CohortCandidate.cohort_id == cohort.id))
        cohort_candidates = cc_res.scalars().all()
        
        # Get recruiter's github token
        conn_res = await session.execute(
            select(GitHubConnection).where(
                GitHubConnection.evaluation_id.in_(
                    select(Evaluation.id).where(Evaluation.recruiter_id == current_user_id)
                )
            ).limit(1)
        )
        conn = conn_res.scalar_one_or_none()
        token = None
        if conn:
            enc_key = os.getenv("ENCRYPTION_KEY")
            sync_svc = GitHubSyncService(enc_key.encode() if enc_key else None)
            try:
                token = sync_svc.decrypt_token(conn.access_token)
            except Exception:
                token = conn.access_token

        # Parse template url
        # e.g. https://github.com/owner/repo
        parts = template.template_repo_url.strip("/").split("/")
        if len(parts) >= 2:
            template_owner = parts[-2]
            template_repo = parts[-1]
        else:
            template_owner = "unknown"
            template_repo = "unknown"

        async with httpx.AsyncClient() as client:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Candidate-Evaluation-Platform"
            }
            if token:
                headers["Authorization"] = f"token {token}"
                
                # Get authenticated user's login to use as owner of new repos
                user_res = await client.get("https://api.github.com/user", headers=headers)
                if user_res.status_code == 200:
                    auth_owner = user_res.json().get("login")
                else:
                    auth_owner = template_owner
            else:
                auth_owner = template_owner
        
            for cc in cohort_candidates:
                cand_res = await session.execute(select(Candidate).where(Candidate.id == cc.candidate_id))
                cand = cand_res.scalar_one_or_none()
                if not cand:
                    continue
                    
                new_repo_name = f"{template_repo}-{cand.github_username}-{cohort.id}"
                
                # Create repo from template if token available
                if token:
                    gen_res = await client.post(
                        f"https://api.github.com/repos/{template_owner}/{template_repo}/generate",
                        headers=headers,
                        json={
                            "owner": auth_owner,
                            "name": new_repo_name,
                            "private": True
                        }
                    )
                    
                    if gen_res.status_code in (200, 201):
                        # Invite candidate
                        await client.put(
                            f"https://api.github.com/repos/{auth_owner}/{new_repo_name}/collaborators/{cand.github_username}",
                            headers=headers,
                            json={"permission": "write"}
                        )
                    else:
                        # Fallback to cand's username if generation failed
                        auth_owner = cand.github_username
                        new_repo_name = template_repo
                else:
                    # Mock behavior if no token
                    auth_owner = cand.github_username
                    new_repo_name = template_repo
                    
                eval_record = Evaluation(
                    recruiter_id=current_user_id,
                    cohort_id=cohort.id,
                    candidate_id=cand.id,
                    repo_owner=auth_owner,
                    repo_name=new_repo_name,
                    status=EvaluationStatus.ACTIVE
                )
                session.add(eval_record)
                
                cand.status = CandidateStatus.IN_COHORT
                
        cohort.is_rubric_locked = True
        await session.commit()


@router.post(
    "/cohorts/{id}/start",
    summary="Start a cohort (forks repos)",
)
async def start_cohort(
    id: int,
    background_tasks: BackgroundTasks,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Cohort).where(Cohort.id == id, Cohort.created_by == current_user.id)
    )
    cohort = res.scalar_one_or_none()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")
        
    if cohort.is_rubric_locked:
        raise HTTPException(status_code=400, detail="Cohort has already been started")
        
    background_tasks.add_task(_run_cohort_start_background, id, current_user.id)
    return {"status": "success", "message": "Cohort started. Repos are being forked in the background."}


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


async def _run_background_sync(evaluation_id: int):
    # Need to run with a fresh session because the current session will be closed
    from main import async_session
    async with async_session() as session:
        conn_res = await session.execute(
            select(GitHubConnection).where(GitHubConnection.evaluation_id == evaluation_id)
        )
        conn = conn_res.scalar_one_or_none()
        if not conn:
            return

        enc_key = os.getenv("ENCRYPTION_KEY")
        sync_svc = GitHubSyncService(enc_key.encode() if enc_key else None)
        try:
            token = sync_svc.decrypt_token(conn.access_token)
        except Exception:
            token = conn.access_token

        await sync_svc.sync_evaluation(session, evaluation_id, token)

@router.post(
    "/evaluations/{id}/activate",
    response_model=EvaluationResponse,
    summary="Activate evaluation",
)
async def activate_evaluation(
    id: int,
    background_tasks: BackgroundTasks,
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
    
    background_tasks.add_task(_run_background_sync, id)
    
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

    conn_res = await db.execute(
        select(GitHubConnection).where(GitHubConnection.evaluation_id == id)
    )
    conn = conn_res.scalar_one_or_none()
    if not conn:
        raise HTTPException(
            status_code=400,
            detail="GitHub connection not established for this evaluation.",
        )

    sync_rate_tracker[id] = now_ts

    enc_key = os.getenv("ENCRYPTION_KEY")
    sync_svc = GitHubSyncService(enc_key.encode() if enc_key else None)
    try:
        token = sync_svc.decrypt_token(conn.access_token)
    except Exception:
        token = conn.access_token

    log = await sync_svc.sync_evaluation(db, id, token)
    return {"status": "success", "message": "Manual sync completed", "log_id": log.id}


@router.get(
    "/evaluations/{id}/timeline",
    response_model=List[TimelineItem],
    summary="Get evaluation activity timeline",
)
async def get_timeline(
    id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    eval_res = await db.execute(
        select(Evaluation).where(Evaluation.id == id, Evaluation.recruiter_id == current_user.id)
    )
    if not eval_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Evaluation not found")

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

    timeline.sort(key=lambda x: x.timestamp, reverse=True)
    return timeline[skip : skip + limit]


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
    
    sb_res = await db.execute(
        select(ScoreBreakdown).where(ScoreBreakdown.evaluation_id == id)
    )
    breakdowns = sb_res.scalars().all()
    
    if breakdowns:
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        
        story.append(Paragraph("Score Breakdown", styles["Heading2"]))
        story.append(Spacer(1, 12))
        
        table_data = [["Metric Name", "Raw Value", "Normalized Score", "Weight"]]
        for b in breakdowns:
            table_data.append([
                b.metric_name.replace("_", " ").title(),
                str(float(b.raw_value)),
                f"{float(b.normalized_score):.2f}",
                f"{float(b.weight):.3f}"
            ])
            
        t = Table(table_data, colWidths=[200, 100, 100, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 18))

    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_card_eval_{id}.pdf"},
    )


# Cohort Hiring Team Views

@router.get(
    "/cohorts/{id}/leaderboard",
    summary="Get cohort leaderboard",
)
async def get_cohort_leaderboard(
    id: int,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    cohort_res = await db.execute(
        select(Cohort).where(Cohort.id == id, Cohort.created_by == current_user.id)
    )
    if not cohort_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Cohort not found")

    evals_res = await db.execute(
        select(Evaluation).where(Evaluation.cohort_id == id)
    )
    evals = evals_res.scalars().all()
    
    leaderboard = []
    for ev in evals:
        cand_res = await db.execute(select(Candidate).where(Candidate.id == ev.candidate_id))
        cand = cand_res.scalar_one()
        leaderboard.append({
            "candidate_id": cand.id,
            "name": cand.name,
            "email": cand.email,
            "github_username": cand.github_username,
            "status": ev.status,
            "final_score": float(ev.final_score) if ev.final_score else None
        })
        
    leaderboard.sort(key=lambda x: (x["final_score"] is None, -(x["final_score"] or 0)))
    return {"leaderboard": leaderboard}


@router.get(
    "/cohorts/{id}/candidates/{candidate_id}/report",
    summary="Get detailed report card for a candidate in a cohort",
)
async def get_candidate_report(
    id: int,
    candidate_id: int,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    cohort_res = await db.execute(
        select(Cohort).where(Cohort.id == id, Cohort.created_by == current_user.id)
    )
    if not cohort_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Cohort not found")

    eval_res = await db.execute(
        select(Evaluation).where(Evaluation.cohort_id == id, Evaluation.candidate_id == candidate_id)
    )
    ev = eval_res.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation for candidate not found in cohort")

    sb_res = await db.execute(
        select(ScoreBreakdown).where(ScoreBreakdown.evaluation_id == ev.id)
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

    return {
        "evaluation_id": ev.id,
        "status": ev.status.value,
        "final_score": float(ev.final_score) if ev.final_score else None,
        "metrics": metrics
    }


@router.get(
    "/cohorts/{id}/compare",
    summary="Compare multiple candidates side-by-side",
)
async def compare_candidates(
    id: int,
    candidates: str = Query(..., description="Comma-separated candidate IDs"),
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    candidate_ids = [int(c) for c in candidates.split(',')]
    
    cohort_res = await db.execute(
        select(Cohort).where(Cohort.id == id, Cohort.created_by == current_user.id)
    )
    if not cohort_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Cohort not found")

    evals_res = await db.execute(
        select(Evaluation).where(Evaluation.cohort_id == id, Evaluation.candidate_id.in_(candidate_ids))
    )
    evals = evals_res.scalars().all()
    
    comparison = {}
    for ev in evals:
        sb_res = await db.execute(
            select(ScoreBreakdown).where(ScoreBreakdown.evaluation_id == ev.id)
        )
        breakdowns = sb_res.scalars().all()
        metrics = {
            b.metric_name: float(b.normalized_score) for b in breakdowns
        }
        comparison[ev.candidate_id] = {
            "final_score": float(ev.final_score) if ev.final_score else None,
            "metrics": metrics
        }
        
    return comparison


@router.get(
    "/cohorts/{id}/candidates/{candidate_id}/evidence",
    summary="Get underlying PRs and commits as evidence",
)
async def get_candidate_evidence(
    id: int,
    candidate_id: int,
    current_user: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db),
):
    cohort_res = await db.execute(
        select(Cohort).where(Cohort.id == id, Cohort.created_by == current_user.id)
    )
    if not cohort_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Cohort not found")

    eval_res = await db.execute(
        select(Evaluation).where(Evaluation.cohort_id == id, Evaluation.candidate_id == candidate_id)
    )
    ev = eval_res.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    prs_res = await db.execute(select(PullRequest).where(PullRequest.evaluation_id == ev.id))
    prs = prs_res.scalars().all()
    
    commits_res = await db.execute(select(Commit).where(Commit.evaluation_id == ev.id))
    commits = commits_res.scalars().all()
    
    return {
        "prs": [{"id": pr.id, "title": pr.title, "url": pr.html_url, "merged_at": pr.merged_at} for pr in prs],
        "commits": [{"id": c.id, "message": c.message, "url": c.html_url, "date": c.committed_at} for c in commits]
    }
