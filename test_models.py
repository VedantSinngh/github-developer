"""
Minimal test to verify models file syntax and SQLAlchemy table metadata.
"""
from models import (
    Base,
    Recruiter,
    RoleProfile,
    Evaluation,
    GitHubConnection,
    Commit,
    CommitFile,
    PullRequest,
    PRReviewer,
    PRComment,
    ScoreBreakdown,
    SyncLog,
    EvaluationStatus,
)

def test_models_metadata():
    tables = Base.metadata.tables
    expected_tables = [
        "recruiters",
        "role_profiles",
        "evaluations",
        "github_connections",
        "commits",
        "commit_files",
        "pull_requests",
        "pr_reviewers",
        "pr_comments",
        "score_breakdown",
        "sync_logs",
    ]
    for table_name in expected_tables:
        assert table_name in tables, f"Table {table_name} missing from metadata"
    print("All models successfully validated.")

if __name__ == "__main__":
    test_models_metadata()
