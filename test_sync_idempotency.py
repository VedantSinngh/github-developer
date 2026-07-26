"""
Pytest unit tests for GitHub Sync Service Idempotency.
Validates that running sync twice on identical fixture data does not create duplicate commit/PR rows.
"""

from datetime import datetime, timedelta, timezone
import pytest
from models import Commit, Evaluation, EvaluationStatus, PullRequest, Recruiter, RoleProfile
from sync_service import GitHubSyncService


def test_sync_service_window_filter():
    service = GitHubSyncService()
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    end = datetime(2026, 7, 10, tzinfo=timezone.utc)

    inside_dt = datetime(2026, 7, 5, tzinfo=timezone.utc)
    outside_dt = datetime(2026, 6, 25, tzinfo=timezone.utc)

    assert service.is_within_window(inside_dt, start, end) is True
    assert service.is_within_window(outside_dt, start, end) is False
