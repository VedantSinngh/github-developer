"""
Updated SQLAlchemy models for Candidate Evaluation Platform.
Adds share_token (UUID) to evaluations table for public read-only shareable score cards.
"""

from datetime import datetime
from decimal import Decimal
import enum
from typing import List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class EvaluationStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    LOCKED = "locked"


class Recruiter(Base):
    __tablename__ = "recruiters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    org_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    evaluations: Mapped[List["Evaluation"]] = relationship("Evaluation", back_populates="recruiter")


class RoleProfile(Base):
    __tablename__ = "role_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    weight_consistency: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    weight_pr_quality: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    weight_review_cycles: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    weight_collaboration: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    weight_stability: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)

    evaluations: Mapped[List["Evaluation"]] = relationship("Evaluation", back_populates="role_profile")


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        CheckConstraint("end_date > start_date", name="check_evaluations_end_after_start"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recruiter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_profile_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("role_profiles.id", ondelete="SET NULL"), nullable=True
    )

    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    candidate_email: Mapped[str] = mapped_column(String(255), nullable=False)
    github_username: Mapped[str] = mapped_column(String(255), nullable=False)
    repo_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(255), nullable=False)

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[EvaluationStatus] = mapped_column(
        Enum(EvaluationStatus, name="evaluation_status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=EvaluationStatus.PENDING,
        server_default=EvaluationStatus.PENDING.value,
        index=True,
    )

    final_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    share_token: Mapped[Optional[str]] = mapped_column(
        String(36), unique=True, nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    recruiter: Mapped["Recruiter"] = relationship("Recruiter", back_populates="evaluations")
    role_profile: Mapped[Optional["RoleProfile"]] = relationship("RoleProfile", back_populates="evaluations")
    github_connection: Mapped[Optional["GitHubConnection"]] = relationship(
        "GitHubConnection", back_populates="evaluation", uselist=False, cascade="all, delete-orphan"
    )

    commits: Mapped[List["Commit"]] = relationship(
        "Commit", back_populates="evaluation", cascade="all, delete-orphan"
    )
    pull_requests: Mapped[List["PullRequest"]] = relationship(
        "PullRequest", back_populates="evaluation", cascade="all, delete-orphan"
    )
    score_breakdowns: Mapped[List["ScoreBreakdown"]] = relationship(
        "ScoreBreakdown", back_populates="evaluation", cascade="all, delete-orphan"
    )
    sync_logs: Mapped[List["SyncLog"]] = relationship(
        "SyncLog", back_populates="evaluation", cascade="all, delete-orphan"
    )


class GitHubConnection(Base):
    __tablename__ = "github_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="github_connection")


class Commit(Base):
    __tablename__ = "commits"
    __table_args__ = (
        Index("idx_commits_eval_committed", "evaluation_id", "committed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False
    )
    sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    author_login: Mapped[str] = mapped_column(String(255), nullable=False)
    committed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    additions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deletions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="commits")
    files: Mapped[List["CommitFile"]] = relationship(
        "CommitFile", back_populates="commit", cascade="all, delete-orphan"
    )


class CommitFile(Base):
    __tablename__ = "commit_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    commit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)

    commit: Mapped["Commit"] = relationship("Commit", back_populates="files")


class PullRequest(Base):
    __tablename__ = "pull_requests"
    __table_args__ = (
        Index("idx_pull_requests_eval_opened", "evaluation_id", "opened_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False
    )
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    author_login: Mapped[str] = mapped_column(String(255), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    merged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    first_review_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    additions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deletions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="pull_requests")
    reviewers: Mapped[List["PRReviewer"]] = relationship(
        "PRReviewer", back_populates="pull_request", cascade="all, delete-orphan"
    )
    comments: Mapped[List["PRComment"]] = relationship(
        "PRComment", back_populates="pull_request", cascade="all, delete-orphan"
    )


class PRReviewer(Base):
    __tablename__ = "pr_reviewers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pr_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_login: Mapped[str] = mapped_column(String(255), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    review_state: Mapped[str] = mapped_column(String(50), nullable=False)

    pull_request: Mapped["PullRequest"] = relationship("PullRequest", back_populates="reviewers")


class PRComment(Base):
    __tablename__ = "pr_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pr_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_login: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    pull_request: Mapped["PullRequest"] = relationship("PullRequest", back_populates="comments")


class ScoreBreakdown(Base):
    __tablename__ = "score_breakdown"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_value: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    normalized_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="score_breakdowns")


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    commits_pulled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prs_pulled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="sync_logs")
