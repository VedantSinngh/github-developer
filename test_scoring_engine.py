"""
Pytest unit tests for Scoring Engine with synthetic commit and PR fixtures.
Covers:
- Solo candidate (collaboration weight redistribution)
- No collaboration signal
- Edge case of zero commits
- Edge case of commit concentration (>60% in last 10% window)
- Edge case of one giant PR (>500 lines)
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from models import Commit, PullRequest, RoleProfile
from scoring_engine import (
    calculate_consistency_score,
    calculate_pr_quality_score,
    compute_final_score,
)

@pytest.fixture
def default_role_profile():
    return RoleProfile(
        id=1,
        name="Senior Backend Engineer",
        description="Standard weights",
        weight_consistency=Decimal("0.200"),
        weight_pr_quality=Decimal("0.250"),
        weight_review_cycles=Decimal("0.200"),
        weight_collaboration=Decimal("0.150"),
        weight_stability=Decimal("0.200"),
    )

def test_zero_commits_edge_case(default_role_profile):
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    end = datetime(2026, 7, 10, tzinfo=timezone.utc)
    
    result = compute_final_score(
        candidate_login="testdev",
        start_date=start,
        end_date=end,
        commits=[],
        commit_files=[],
        prs=[],
        all_prs=[],
        reviewers=[],
        comments=[],
        role_profile=default_role_profile,
    )
    
    assert result["metrics"]["consistency"]["normalized"] == 0.0
    assert result["metrics"]["pr_quality"]["normalized"] == 0.0
    assert result["is_solo"] is True
    # Collaboration weight should redistribute to 0
    assert result["metrics"]["collaboration"]["weight"] == 0.0

def test_commit_concentration_penalty(default_role_profile):
    start = datetime(2026, 7, 1, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 7, 11, 0, 0, tzinfo=timezone.utc) # 10 days
    
    # 1 commit early, 9 commits in final 2 hours (last 10% of 10 days = final 24h)
    early_commit = Commit(id=1, sha="abc1", committed_at=start + timedelta(days=1), additions=10, deletions=5, message="m1")
    late_time = end - timedelta(hours=2)
    late_commits = [
        Commit(id=i, sha=f"sha{i}", committed_at=late_time + timedelta(minutes=i), additions=10, deletions=5, message="m")
        for i in range(2, 11)
    ]
    all_commits = [early_commit] + late_commits

    raw, norm = calculate_consistency_score(all_commits, start, end)
    # Active days ratio: 2 active days out of 11 = 2/11 = ~0.18 -> raw score 18.18
    # Late ratio: 9/10 = 90% in last 10% window (>60%). Penalty = (0.9 - 0.6) * 100 = 30 points
    # Norm score drops to 0.0 due to heavy penalty
    assert norm == 0.0

def test_giant_pr_penalty():
    pr = PullRequest(
        id=1,
        pr_number=101,
        author_login="candidate",
        opened_at=datetime.now(timezone.utc),
        additions=2000,
        deletions=1500,
    )
    raw_loc, norm_score = calculate_pr_quality_score([pr])
    assert raw_loc == 3500.0
    # Heavily penalized for >500 LOC
    assert norm_score < 30.0

def test_solo_candidate_collaboration_redistribution(default_role_profile):
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    end = datetime(2026, 7, 5, tzinfo=timezone.utc)

    commit = Commit(id=1, sha="c1", committed_at=start + timedelta(days=1), additions=100, deletions=20, message="m")
    pr = PullRequest(
        id=1,
        pr_number=1,
        author_login="solodev",
        opened_at=start + timedelta(days=1),
        merged_at=start + timedelta(days=2),
        additions=150,
        deletions=20,
    )

    result = compute_final_score(
        candidate_login="solodev",
        start_date=start,
        end_date=end,
        commits=[commit],
        commit_files=[],
        prs=[pr],
        all_prs=[pr], # Solo candidate only
        reviewers=[],
        comments=[],
        role_profile=default_role_profile,
    )

    assert result["is_solo"] is True
    assert result["metrics"]["collaboration"]["weight"] == 0.0
    # Total sum of other weights should equal 1.0 after redistribution
    other_weights_sum = (
        result["metrics"]["consistency"]["weight"]
        + result["metrics"]["pr_quality"]["weight"]
        + result["metrics"]["review_cycles"]["weight"]
        + result["metrics"]["stability"]["weight"]
    )
    assert round(other_weights_sum, 3) == 1.0
