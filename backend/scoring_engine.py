"""
Scoring Engine for Candidate Evaluation Platform.
Pure functional core for computing candidate performance metrics via SQL and persisting scores into an immutable ledger.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict
from sqlalchemy import select, func, text
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Commit,
    CommitFile,
    Evaluation,
    EvaluationStatus,
    PRComment,
    PRReviewer,
    PullRequest,
    RoleProfile,
    ScoreBreakdown,
    Cohort,
)


class AlreadyLockedException(Exception):
    """Raised when trying to mutate or persist score for an already locked evaluation."""
    pass


async def compute_sql_signals(session: AsyncSession, evaluation_id: int, start_date: datetime) -> Dict[str, float]:
    """Computes all signals via SQL."""
    # 1. PRs opened & merged
    pr_stats_res = await session.execute(
        select(
            func.count(PullRequest.id).label("opened"),
            func.count(PullRequest.merged_at).label("merged")
        ).where(PullRequest.evaluation_id == evaluation_id)
    )
    pr_counts = pr_stats_res.one()
    total_prs = pr_counts.opened or 0
    merged_prs = pr_counts.merged or 0

    # 2. Time to first commit
    first_commit_res = await session.execute(
        select(func.min(Commit.committed_at)).where(Commit.evaluation_id == evaluation_id)
    )
    first_commit = first_commit_res.scalar()
    time_to_first_commit_sec = 0.0
    if first_commit:
        if first_commit.tzinfo is None:
            first_commit = first_commit.replace(tzinfo=timezone.utc)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        time_to_first_commit_sec = (first_commit - start_date).total_seconds()
        
    # 3. PR review turnaround (avg per candidate)
    review_stats = await session.execute(
        select(func.avg(
            func.extract('epoch', PullRequest.first_review_at - PullRequest.opened_at)
        )).where(
            PullRequest.evaluation_id == evaluation_id,
            PullRequest.first_review_at.is_not(None)
        )
    )
    avg_review_sec = review_stats.scalar() or 0.0

    # 4. Commit message quality heuristic (length + regex pattern match)
    # Using ~ for postgres regex match on conventional commits
    conv_commits_res = await session.execute(
        select(func.count(Commit.id)).where(
            Commit.evaluation_id == evaluation_id,
            Commit.message.op('~')('^(feat|fix|docs|style|refactor|perf|test|chore)(\\(.+\\))?: ')
        )
    )
    conv_commits = conv_commits_res.scalar() or 0
    
    total_commits_res = await session.execute(
        select(func.count(Commit.id)).where(Commit.evaluation_id == evaluation_id)
    )
    total_commits = total_commits_res.scalar() or 1
    commit_quality_ratio = conv_commits / max(1, total_commits)

    # 5. Issues closed vs opened ratio (using PRs as issues)
    closed_prs_res = await session.execute(
        select(func.count(PullRequest.id)).where(
            PullRequest.evaluation_id == evaluation_id,
            PullRequest.closed_at.is_not(None)
        )
    )
    closed_prs = closed_prs_res.scalar() or 0
    close_ratio = closed_prs / max(1, total_prs)

    # 6. Comment count on issues/PRs
    comment_count_res = await session.execute(
        select(func.count(PRComment.id))
        .join(PullRequest)
        .where(PullRequest.evaluation_id == evaluation_id)
    )
    comment_count = comment_count_res.scalar() or 0

    # 7. Code churn (self-churn)
    c1 = aliased(Commit)
    c2 = aliased(Commit)
    f1 = aliased(CommitFile)
    f2 = aliased(CommitFile)
    
    churn_res = await session.execute(
        select(func.sum(c1.additions + c1.deletions))
        .select_from(c1)
        .join(f1, c1.id == f1.commit_id)
        .join(f2, (f1.filename == f2.filename) & (f1.commit_id != f2.commit_id))
        .join(c2, f2.commit_id == c2.id)
        .where(
            c1.evaluation_id == evaluation_id,
            c2.evaluation_id == evaluation_id,
            c1.author_login == c2.author_login,
            c1.committed_at > c2.committed_at,
            func.extract('epoch', c1.committed_at - c2.committed_at) <= 7 * 86400
        )
    )
    churn_lines = float(churn_res.scalar() or 0)
    
    return {
        "pr_merged_ratio": merged_prs / max(1, total_prs),
        "time_to_first_commit_sec": time_to_first_commit_sec,
        "avg_review_sec": float(avg_review_sec),
        "commit_quality_ratio": float(commit_quality_ratio),
        "close_ratio": float(close_ratio),
        "comment_count": float(comment_count),
        "churn_lines": churn_lines,
    }

async def persist_score(session: AsyncSession, evaluation_id: int) -> Evaluation:
    stmt = select(Evaluation).where(Evaluation.id == evaluation_id)
    res = await session.execute(stmt)
    evaluation = res.scalar_one_or_none()

    if not evaluation:
        raise ValueError(f"Evaluation {evaluation_id} not found.")

    if evaluation.status == EvaluationStatus.LOCKED:
        raise AlreadyLockedException(f"Evaluation {evaluation_id} is already locked.")

    existing_sb_res = await session.execute(
        select(ScoreBreakdown).where(ScoreBreakdown.evaluation_id == evaluation_id)
    )
    if existing_sb_res.scalars().first():
        raise AlreadyLockedException(f"Score breakdown for evaluation {evaluation_id} already exists in ledger.")

    cohort_res = await session.execute(select(Cohort).where(Cohort.id == evaluation.cohort_id))
    cohort = cohort_res.scalar_one()

    rp_res = await session.execute(
        select(RoleProfile).where(RoleProfile.id == cohort.role_profile_id)
    )
    role_profile = rp_res.scalar_one_or_none() or RoleProfile(
        weight_consistency=Decimal("0.2"),
        weight_pr_quality=Decimal("0.2"),
        weight_review_cycles=Decimal("0.2"),
        weight_collaboration=Decimal("0.2"),
        weight_stability=Decimal("0.2"),
    )

    signals = await compute_sql_signals(session, evaluation_id, cohort.start_date)
    
    # Normalize signals to 0-100 scores
    norm_cons = max(0.0, 100.0 - (signals["time_to_first_commit_sec"] / 3600.0)) # Penalize slower first commits
    norm_pr = signals["pr_merged_ratio"] * 100.0
    norm_rev = max(0.0, 100.0 - (signals["avg_review_sec"] / 3600.0)) # Penalize slow reviews
    norm_collab = min(100.0, signals["comment_count"] * 10.0)
    norm_stab = max(0.0, 100.0 - (signals["churn_lines"] / 10.0)) # Penalize high churn
    
    w_cons = float(role_profile.weight_consistency)
    w_pr = float(role_profile.weight_pr_quality)
    w_rev = float(role_profile.weight_review_cycles)
    w_collab = float(role_profile.weight_collaboration)
    w_stab = float(role_profile.weight_stability)

    final_score = (
        (norm_cons * w_cons) +
        (norm_pr * w_pr) +
        (norm_rev * w_rev) +
        (norm_collab * w_collab) +
        (norm_stab * w_stab)
    )
    final_score = round(max(0.0, min(100.0, final_score)), 2)

    now = datetime.now(timezone.utc)
    
    metrics = {
        "consistency": {"raw": signals["time_to_first_commit_sec"], "normalized": norm_cons, "weight": w_cons},
        "pr_quality": {"raw": signals["pr_merged_ratio"], "normalized": norm_pr, "weight": w_pr},
        "review_cycles": {"raw": signals["avg_review_sec"], "normalized": norm_rev, "weight": w_rev},
        "collaboration": {"raw": signals["comment_count"], "normalized": norm_collab, "weight": w_collab},
        "stability": {"raw": signals["churn_lines"], "normalized": norm_stab, "weight": w_stab},
    }

    for metric_name, data in metrics.items():
        breakdown_entry = ScoreBreakdown(
            evaluation_id=evaluation.id,
            metric_name=metric_name,
            raw_value=Decimal(str(data["raw"])),
            normalized_score=Decimal(str(data["normalized"])),
            weight=Decimal(str(data["weight"])),
            computed_at=now,
            is_locked=True,
        )
        session.add(breakdown_entry)

    evaluation.final_score = Decimal(str(final_score))
    evaluation.status = EvaluationStatus.LOCKED
    evaluation.locked_at = now

    await session.commit()
    return evaluation
