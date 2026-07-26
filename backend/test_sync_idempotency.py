"""
Pytest unit tests for GitHub Sync Service Idempotency.
Validates that running sync twice on identical fixture data does not create duplicate commit/PR rows.
"""

from datetime import datetime, timedelta, timezone
import pytest
from models import Commit, Evaluation, EvaluationStatus, PullRequest, Recruiter, RoleProfile
from sync_service import GitHubSyncService
from main import async_session
from sqlalchemy import select
from unittest.mock import AsyncMock, patch


def test_sync_service_window_filter():
    service = GitHubSyncService()
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    end = datetime(2026, 7, 10, tzinfo=timezone.utc)

    inside_dt = datetime(2026, 7, 5, tzinfo=timezone.utc)
    outside_dt = datetime(2026, 6, 25, tzinfo=timezone.utc)

    assert service.is_within_window(inside_dt, start, end) is True
    assert service.is_within_window(outside_dt, start, end) is False

@pytest.mark.asyncio
async def test_sync_idempotency_duplicate_run():
    service = GitHubSyncService()
    
    # We will mock execute_graphql to return a fixed set of commits and PRs
    mock_data = {
        "data": {
            "repository": {
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "pageInfo": {"hasNextPage": False},
                            "nodes": [
                                {
                                    "sha": "a1b2c3d4",
                                    "message": "init",
                                    "committedDate": "2026-07-05T12:00:00Z",
                                    "additions": 10,
                                    "deletions": 2,
                                    "author": {"user": {"login": "testuser"}}
                                }
                            ]
                        }
                    }
                },
                "pullRequests": {
                    "pageInfo": {"hasNextPage": False},
                    "nodes": [
                        {
                            "number": 1,
                            "createdAt": "2026-07-05T13:00:00Z",
                            "mergedAt": "2026-07-06T13:00:00Z",
                            "closedAt": "2026-07-06T13:00:00Z",
                            "additions": 50,
                            "deletions": 5,
                            "author": {"login": "testuser"},
                            "reviews": {"nodes": []},
                            "comments": {"nodes": []}
                        }
                    ]
                }
            }
        }
    }
    
    async with async_session() as session:
        # Create minimal dependencies
        recruiter = Recruiter(email="idem@example.com", hashed_password="pw", org_name="Org")
        session.add(recruiter)
        await session.flush()
        
        evaluation = Evaluation(
            recruiter_id=recruiter.id,
            candidate_name="Idem Tester",
            candidate_email="idem@test.com",
            github_username="testuser",
            repo_owner="org",
            repo_name="repo",
            start_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 7, 10, tzinfo=timezone.utc),
        )
        session.add(evaluation)
        await session.commit()
        await session.refresh(evaluation)
        
        with patch.object(service, "execute_graphql", new_callable=AsyncMock) as mock_gql:
            mock_gql.return_value = mock_data
            
            # Run 1
            await service.sync_evaluation(session, evaluation.id, "fake_token")
            
            commits_run1 = (await session.execute(select(Commit).where(Commit.evaluation_id == evaluation.id))).scalars().all()
            prs_run1 = (await session.execute(select(PullRequest).where(PullRequest.evaluation_id == evaluation.id))).scalars().all()
            
            assert len(commits_run1) == 1
            assert len(prs_run1) == 1
            
            # Run 2 - identical data
            await service.sync_evaluation(session, evaluation.id, "fake_token")
            
            commits_run2 = (await session.execute(select(Commit).where(Commit.evaluation_id == evaluation.id))).scalars().all()
            prs_run2 = (await session.execute(select(PullRequest).where(PullRequest.evaluation_id == evaluation.id))).scalars().all()
            
            # Assert counts haven't changed (Idempotency)
            assert len(commits_run2) == 1
            assert len(prs_run2) == 1
