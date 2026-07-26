"""
Scoring Engine for Candidate Evaluation Platform.
Pure functional core for computing candidate performance metrics and persisting scores into an immutable ledger.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Commit,
    Evaluation,
    EvaluationStatus,
    PRComment,
    PRReviewer,
    PullRequest,
    RoleProfile,
    ScoreBreakdown,
)


class AlreadyLockedException(Exception):
    """Raised when trying to mutate or persist score for an already locked evaluation."""
    pass


def calculate_consistency_score(
    commits: List[Commit], start_date: datetime, end_date: datetime
) -> Tuple[float, float]:
    """
    Consistency score (0-100):
    - Active days ratio = active_days / total_days
    - Penalizes last 10% window commit concentration (>60% commits in final 10% window = heavy penalty).
    """
    if not commits:
        return 0.0, 0.0

    total_duration = (end_date - start_date).total_seconds()
    if total_duration <= 0:
        return 0.0, 0.0

    total_days = max(1, (end_date.date() - start_date.date()).days + 1)
    unique_active_days = len(set(c.committed_at.date() for c in commits))
    active_ratio = unique_active_days / total_days

    # Check concentration in final 10% of window
    threshold_time = start_date.timestamp() + (total_duration * 0.9)
    late_commits = sum(1 for c in commits if c.committed_at.timestamp() >= threshold_time)
    late_ratio = late_commits / len(commits)

    raw_score = active_ratio * 100.0
    penalty = 0.0
    if late_ratio > 0.6:
        # Heavy penalty above 60% concentration in final 10% time window
        penalty = (late_ratio - 0.6) * 100.0

    normalized_score = max(0.0, min(100.0, raw_score - penalty))
    return float(active_ratio), float(normalized_score)


def calculate_pr_quality_score(prs: List[PullRequest]) -> Tuple[float, float]:
    """
    PR Quality score (0-100):
    - Normalizes PR line size (ideal additions+deletions: 50 - 500 lines).
    - Factors in whether PRs merged cleanly vs closed without merge.
    """
    if not prs:
        return 0.0, 0.0

    scores = []
    total_loc_list = []
    for pr in prs:
        loc = pr.additions + pr.deletions
        total_loc_list.append(loc)

        # Size score calculation
        if 50 <= loc <= 500:
            size_score = 100.0
        elif loc < 50:
            size_score = max(20.0, (loc / 50.0) * 100.0)
        else:
            # Penalize huge PRs (>500 lines)
            size_score = max(10.0, 100.0 - ((loc - 500) / 20.0))

        # Merge multiplier
        merge_factor = 1.0 if pr.merged_at else (0.3 if pr.closed_at else 0.7)
        scores.append(size_score * merge_factor)

    avg_raw_loc = float(sum(total_loc_list) / len(total_loc_list))
    normalized_score = max(0.0, min(100.0, sum(scores) / len(scores)))
    return avg_raw_loc, normalized_score


def calculate_review_cycles_score(
    prs: List[PullRequest], reviewers: List[PRReviewer]
) -> Tuple[float, float]:
    """
    Review Cycles score (0-100):
    - Fewer CHANGES_REQUESTED rounds before merge = higher score.
    """
    if not prs:
        return 0.0, 100.0  # Default neutral score if no PRs exist

    pr_id_set = {pr.id for pr in prs}
    pr_reviewers = [r for r in reviewers if r.pr_id in pr_id_set]

    changes_requested_count = sum(
        1 for r in pr_reviewers if r.review_state.upper() == "CHANGES_REQUESTED"
    )
    raw_avg_changes = changes_requested_count / len(prs)

    # 0 changes requested = 100%, each change request deducts 25 points
    normalized_score = max(0.0, 100.0 - (raw_avg_changes * 25.0))
    return float(raw_avg_changes), float(normalized_score)


def calculate_collaboration_score(
    candidate_login: str,
    all_prs: List[PullRequest],
    reviewers: List[PRReviewer],
    comments: List[PRComment],
) -> Tuple[float, float, bool]:
    """
    Collaboration score (0-100):
    - Comments/reviews the candidate gave on OTHER candidates' PRs.
    - If solo candidate evaluation (no PRs from others), returns is_solo = True.
    """
    other_prs = [pr for pr in all_prs if pr.author_login != candidate_login]

    if not other_prs:
        # Solo evaluation detected -> weight redistributes proportionally
        return 0.0, 0.0, True

    other_pr_ids = {pr.id for pr in other_prs}

    # Count reviews and comments candidate performed on others' PRs
    reviews_given = sum(
        1 for r in reviewers if r.pr_id in other_pr_ids and r.reviewer_login == candidate_login
    )
    comments_given = sum(
        1 for c in comments if c.pr_id in other_pr_ids and c.author_login == candidate_login
    )

    total_interactions = reviews_given + comments_given
    # Benchmark: 5+ interactions = 100%
    normalized_score = min(100.0, (total_interactions / 5.0) * 100.0)
    return float(total_interactions), float(normalized_score), False


def calculate_stability_score(commits: List[Commit], commit_files: List[Tuple[int, str]]) -> Tuple[float, float]:
    """
    Stability/churn score (0-100):
    - Inverse of churn (files touched 5+ times in <2 weeks by candidate = penalty).
    """
    if not commits or not commit_files:
        return 0.0, 100.0

    file_counts: Dict[str, int] = {}
    for _, filename in commit_files:
        file_counts[filename] = file_counts.get(filename, 0) + 1

    churned_files = sum(1 for fname, count in file_counts.items() if count >= 5)
    total_files = len(file_counts)
    churn_ratio = churned_files / max(1, total_files)

    raw_churn_metric = float(churned_files)
    normalized_score = max(0.0, 100.0 - (churn_ratio * 100.0))
    return raw_churn_metric, normalized_score


def compute_final_score(
    candidate_login: str,
    start_date: datetime,
    end_date: datetime,
    commits: List[Commit],
    commit_files: List[Tuple[int, str]],
    prs: List[PullRequest],
    all_prs: List[PullRequest],
    reviewers: List[PRReviewer],
    comments: List[PRComment],
    role_profile: RoleProfile,
) -> Dict[str, Any]:
    """
    Pure computation of 5 metrics and final weighted score.
    Dynamically redistributes collaboration weight if it's a solo evaluation.
    """
    raw_cons, norm_cons = calculate_consistency_score(commits, start_date, end_date)
    raw_pr, norm_pr = calculate_pr_quality_score(prs)
    raw_rev, norm_rev = calculate_review_cycles_score(prs, reviewers)
    raw_collab, norm_collab, is_solo = calculate_collaboration_score(
        candidate_login, all_prs, reviewers, comments
    )
    raw_stab, norm_stab = calculate_stability_score(commits, commit_files)

    # Weights from role profile
    w_cons = float(role_profile.weight_consistency)
    w_pr = float(role_profile.weight_pr_quality)
    w_rev = float(role_profile.weight_review_cycles)
    w_collab = float(role_profile.weight_collaboration)
    w_stab = float(role_profile.weight_stability)

    if is_solo and w_collab > 0:
        # Redistribute collaboration weight proportionally among remaining 4 signals
        remaining_sum = w_cons + w_pr + w_rev + w_stab
        if remaining_sum > 0:
            w_cons += (w_cons / remaining_sum) * w_collab
            w_pr += (w_pr / remaining_sum) * w_collab
            w_rev += (w_rev / remaining_sum) * w_collab
            w_stab += (w_stab / remaining_sum) * w_collab
            w_collab = 0.0

    final_score = (
        (norm_cons * w_cons)
        + (norm_pr * w_pr)
        + (norm_rev * w_rev)
        + (norm_collab * w_collab)
        + (norm_stab * w_stab)
    )
    final_score = round(max(0.0, min(100.0, final_score)), 2)

    return {
        "final_score": final_score,
        "is_solo": is_solo,
        "metrics": {
            "consistency": {"raw": raw_cons, "normalized": round(norm_cons, 2), "weight": round(w_cons, 3)},
            "pr_quality": {"raw": raw_pr, "normalized": round(norm_pr, 2), "weight": round(w_pr, 3)},
            "review_cycles": {"raw": raw_rev, "normalized": round(norm_rev, 2), "weight": round(w_rev, 3)},
            "collaboration": {"raw": raw_collab, "normalized": round(norm_collab, 2), "weight": round(w_collab, 3)},
            "stability": {"raw": raw_stab, "normalized": round(norm_stab, 2), "weight": round(w_stab, 3)},
        },
    }


async def persist_score(session: AsyncSession, evaluation_id: int) -> Evaluation:
    """
    Fetches evaluation data, computes final score, writes to score_breakdown ledger, and locks evaluation.
    Raises AlreadyLockedException if evaluation is already locked.
    """
    stmt = select(Evaluation).where(Evaluation.id == evaluation_id)
    res = await session.execute(stmt)
    evaluation = res.scalar_one_or_none()

    if not evaluation:
        raise ValueError(f"Evaluation {evaluation_id} not found.")

    if evaluation.status == EvaluationStatus.LOCKED:
        raise AlreadyLockedException(f"Evaluation {evaluation_id} is already locked.")

    # Get role profile
    if not evaluation.role_profile_id:
        raise ValueError(f"Evaluation {evaluation_id} has no role profile assigned.")

    rp_res = await session.execute(
        select(RoleProfile).where(RoleProfile.id == evaluation.role_profile_id)
    )
    role_profile = rp_res.scalar_one_or_none()

    # Load data for evaluation
    commits_res = await session.execute(
        select(Commit).where(Commit.evaluation_id == evaluation_id)
    )
    commits = list(commits_res.scalars().all())

    prs_res = await session.execute(
        select(PullRequest).where(PullRequest.evaluation_id == evaluation_id)
    )
    prs = list(prs_res.scalars().all())

    rev_res = await session.execute(
        select(PRReviewer).join(PullRequest).where(PullRequest.evaluation_id == evaluation_id)
    )
    reviewers = list(rev_res.scalars().all())

    comm_res = await session.execute(
        select(PRComment).join(PullRequest).where(PullRequest.evaluation_id == evaluation_id)
    )
    comments = list(comm_res.scalars().all())

    # Compute score breakdown
    computed = compute_final_score(
        candidate_login=evaluation.github_username,
        start_date=evaluation.start_date,
        end_date=evaluation.end_date,
        commits=commits,
        commit_files=[],
        prs=prs,
        all_prs=prs,
        reviewers=reviewers,
        comments=comments,
        role_profile=role_profile,
    )

    now = datetime.now(timezone.utc)

    # Insert into score_breakdown
    for metric_name, data in computed["metrics"].items():
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

    evaluation.final_score = Decimal(str(computed["final_score"]))
    evaluation.status = EvaluationStatus.LOCKED
    evaluation.locked_at = now

    await session.commit()
    return evaluation
