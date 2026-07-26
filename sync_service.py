"""
GitHub Sync Service for Candidate Evaluation Platform.
Uses GraphQL API with cursor pagination, rate limit management, window-bounded filtering, structured logging, idempotent upserts, and auto-transition to locked ledger.
"""

import asyncio
from datetime import datetime, timezone
import logging

import json
from typing import Any, Dict, List, Optional
import uuid
from cryptography.fernet import Fernet
import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Commit,
    CommitFile,
    Evaluation,
    EvaluationStatus,
    GitHubConnection,
    PRComment,
    PRReviewer,
    PullRequest,
    SyncLog,
)
from scoring_engine import persist_score

# Structured JSON Logger
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "evaluation_id"):
            log_obj["evaluation_id"] = record.evaluation_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

logger = logging.getLogger("github_sync")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

GRAPHQL_URL = "https://api.github.com/graphql"

FETCH_REPO_ACTIVITY_QUERY = """
query GetRepoActivity(
  $owner: String!
  $name: String!
  $commitsCursor: String
  $prsCursor: String
) {
  rateLimit {
    remaining
    resetAt
  }
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $commitsCursor) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              sha: oid
              message
              committedDate
              additions
              deletions
              author {
                user {
                  login
                }
              }
            }
          }
        }
      }
    }
    pullRequests(first: 50, after: $prsCursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        createdAt
        mergedAt
        closedAt
        additions
        deletions
        author {
          login
        }
        reviews(first: 50) {
          nodes {
            author {
              login
            }
            createdAt
            state
          }
        }
        comments(first: 50) {
          nodes {
            author {
              login
            }
            createdAt
          }
        }
      }
    }
  }
}
"""


class GitHubSyncService:
    def __init__(self, secret_key: Optional[bytes] = None):
        if secret_key:
            self.cipher = Fernet(secret_key)
        else:
            self.cipher = None

    def decrypt_token(self, encrypted_token: str) -> str:
        if self.cipher:
            return self.cipher.decrypt(encrypted_token.encode()).decode()
        return encrypted_token

    def parse_iso_dt(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    def is_within_window(self, dt: datetime, start_date: datetime, end_date: datetime) -> bool:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        return start_date <= dt <= end_date

    async def execute_graphql(
        self, token: str, query: str, variables: Dict[str, Any], evaluation_id: int
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Candidate-Evaluation-Platform",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            for attempt in range(3):
                response = await client.post(
                    GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers
                )
                rate_remaining = response.headers.get("X-RateLimit-Remaining")
                if rate_remaining and int(rate_remaining) < 10:
                    logger.warning(
                        f"GitHub rate limit low ({rate_remaining}). Backing off...",
                        extra={"evaluation_id": evaluation_id},
                    )
                    await asyncio.sleep(2 ** (attempt + 1))

                if response.status_code == 200:
                    data = response.json()
                    if "errors" in data:
                        logger.error(
                            f"GraphQL Errors: {data['errors']}",
                            extra={"evaluation_id": evaluation_id},
                        )
                    return data
                elif response.status_code in [403, 429]:
                    await asyncio.sleep(2 ** (attempt + 1))
                else:
                    logger.error(
                        f"GitHub API HTTP error: {response.status_code}",
                        extra={"evaluation_id": evaluation_id},
                    )
                    response.raise_for_status()

            raise Exception("GitHub API request failed after exponential retries.")

    async def sync_evaluation(
        self, session: AsyncSession, evaluation_id: int, access_token: str
    ) -> SyncLog:
        logger.info("Sync started", extra={"evaluation_id": evaluation_id})

        stmt = select(Evaluation).where(Evaluation.id == evaluation_id)
        res = await session.execute(stmt)
        evaluation = res.scalar_one_or_none()
        if not evaluation:
            raise ValueError(f"Evaluation {evaluation_id} not found.")

        now = datetime.now(timezone.utc)
        start_date = evaluation.start_date
        end_date = evaluation.end_date

        sync_log = SyncLog(
            evaluation_id=evaluation.id,
            started_at=now,
            status="in_progress",
            commits_pulled=0,
            prs_pulled=0,
        )
        session.add(sync_log)
        await session.commit()

        try:
            commits_pulled = 0
            prs_pulled = 0
            commits_cursor = None
            prs_cursor = None
            has_more_commits = True
            has_more_prs = True

            while has_more_commits or has_more_prs:
                variables = {
                    "owner": evaluation.repo_owner,
                    "name": evaluation.repo_name,
                    "commitsCursor": commits_cursor if has_more_commits else None,
                    "prsCursor": prs_cursor if has_more_prs else None,
                }

                response_data = await self.execute_graphql(
                    access_token, FETCH_REPO_ACTIVITY_QUERY, variables, evaluation_id
                )
                repo_data = response_data.get("data", {}).get("repository", {})
                if not repo_data:
                    break

                # Process Commits with Idempotent Upsert
                history_data = repo_data.get("defaultBranchRef", {}).get("target", {}).get("history", {})
                commit_nodes = history_data.get("nodes", [])
                for node in commit_nodes:
                    committed_at = self.parse_iso_dt(node.get("committedDate"))
                    author_user = node.get("author", {}).get("user", {})
                    author_login = author_user.get("login") if author_user else "unknown"

                    # WINDOW-BOUNDED FILTER: strictly inside [start_date, end_date]
                    if committed_at and self.is_within_window(committed_at, start_date, end_date):
                        # Idempotent Upsert using sha & evaluation_id
                        c_stmt = select(Commit).where(
                            Commit.evaluation_id == evaluation.id, Commit.sha == node["sha"]
                        )
                        c_res = await session.execute(c_stmt)
                        existing_commit = c_res.scalar_one_or_none()

                        if not existing_commit:
                            commit_obj = Commit(
                                evaluation_id=evaluation.id,
                                sha=node["sha"],
                                author_login=author_login,
                                committed_at=committed_at,
                                additions=node.get("additions", 0),
                                deletions=node.get("deletions", 0),
                                message=node.get("message", ""),
                            )
                            session.add(commit_obj)
                            commits_pulled += 1
                        else:
                            existing_commit.additions = node.get("additions", 0)
                            existing_commit.deletions = node.get("deletions", 0)

                commit_page_info = history_data.get("pageInfo", {})
                has_more_commits = commit_page_info.get("hasNextPage", False)
                commits_cursor = commit_page_info.get("endCursor")

                # Process Pull Requests with Idempotent Upsert
                prs_data = repo_data.get("pullRequests", {})
                pr_nodes = prs_data.get("nodes", [])
                for pr_node in pr_nodes:
                    opened_at = self.parse_iso_dt(pr_node.get("createdAt"))
                    merged_at = self.parse_iso_dt(pr_node.get("mergedAt"))
                    closed_at = self.parse_iso_dt(pr_node.get("closedAt"))
                    author_login = pr_node.get("author", {}).get("login", "unknown")

                    if opened_at and self.is_within_window(opened_at, start_date, end_date):
                        pr_stmt = select(PullRequest).where(
                            PullRequest.evaluation_id == evaluation.id,
                            PullRequest.pr_number == pr_node["number"],
                        )
                        pr_res = await session.execute(pr_stmt)
                        existing_pr = pr_res.scalar_one_or_none()

                        reviews = pr_node.get("reviews", {}).get("nodes", [])
                        review_dts = [
                            self.parse_iso_dt(r.get("createdAt"))
                            for r in reviews
                            if r.get("createdAt")
                        ]
                        first_review_at = min(review_dts) if review_dts else None

                        if not existing_pr:
                            pr_obj = PullRequest(
                                evaluation_id=evaluation.id,
                                pr_number=pr_node["number"],
                                author_login=author_login,
                                opened_at=opened_at,
                                merged_at=merged_at,
                                closed_at=closed_at,
                                first_review_at=first_review_at,
                                additions=pr_node.get("additions", 0),
                                deletions=pr_node.get("deletions", 0),
                            )
                            session.add(pr_obj)
                            await session.flush()
                            existing_pr = pr_obj
                            prs_pulled += 1
                        else:
                            existing_pr.merged_at = merged_at
                            existing_pr.closed_at = closed_at
                            existing_pr.first_review_at = first_review_at
                            existing_pr.additions = pr_node.get("additions", 0)
                            existing_pr.deletions = pr_node.get("deletions", 0)

                        for rev in reviews:
                            rev_at = self.parse_iso_dt(rev.get("createdAt"))
                            rev_author = rev.get("author", {}).get("login", "unknown")
                            if rev_at and self.is_within_window(rev_at, start_date, end_date):
                                session.add(
                                    PRReviewer(
                                        pr_id=existing_pr.id,
                                        reviewer_login=rev_author,
                                        reviewed_at=rev_at,
                                        review_state=rev.get("state", "COMMENTED"),
                                    )
                                )

                        comments = pr_node.get("comments", {}).get("nodes", [])
                        for comm in comments:
                            comm_at = self.parse_iso_dt(comm.get("createdAt"))
                            comm_author = comm.get("author", {}).get("login", "unknown")
                            if comm_at and self.is_within_window(comm_at, start_date, end_date):
                                session.add(
                                    PRComment(
                                        pr_id=existing_pr.id,
                                        author_login=comm_author,
                                        created_at=comm_at,
                                    )
                                )

                pr_page_info = prs_data.get("pageInfo", {})
                has_more_prs = pr_page_info.get("hasNextPage", False)
                prs_cursor = pr_page_info.get("endCursor")

            sync_log.status = "success"
            sync_log.finished_at = datetime.now(timezone.utc)
            sync_log.commits_pulled = commits_pulled
            sync_log.prs_pulled = prs_pulled
            await session.commit()
            logger.info("Sync finished successfully", extra={"evaluation_id": evaluation_id})
            return sync_log

        except Exception as e:
            sync_log.status = "failed"
            sync_log.finished_at = datetime.now(timezone.utc)
            sync_log.error_message = str(e)
            await session.commit()
            logger.error(
                f"Sync failed with error: {str(e)}", extra={"evaluation_id": evaluation_id}
            )
            raise


async def run_auto_lock_transition_job(session: AsyncSession, sync_service: GitHubSyncService):
    """
    Scheduled job: Finds all evaluations where status='active' AND NOW() > end_date.
    Transitions status -> 'completed', runs final sync, computes final score + persist_score(),
    generates share_token, and locks the evaluation.
    """
    now = datetime.now(timezone.utc)
    stmt = select(Evaluation).where(
        Evaluation.status == EvaluationStatus.ACTIVE, Evaluation.end_date < now
    )
    res = await session.execute(stmt)
    expired_evaluations = res.scalars().all()

    for evaluation in expired_evaluations:
        logger.info("Auto-lock transition initiated", extra={"evaluation_id": evaluation.id})
        evaluation.status = EvaluationStatus.COMPLETED
        await session.commit()

        # Run final sync if connection exists
        conn_res = await session.execute(
            select(GitHubConnection).where(GitHubConnection.evaluation_id == evaluation.id)
        )
        conn = conn_res.scalar_one_or_none()
        if conn:
            token = sync_service.decrypt_token(conn.access_token)
            await sync_service.sync_evaluation(session, evaluation.id, token)

        # Generate share token and lock ledger
        evaluation.share_token = str(uuid.uuid4())
        await persist_score(session, evaluation.id)
        logger.info(
            "Evaluation score locked successfully into immutable ledger",
            extra={"evaluation_id": evaluation.id},
        )
