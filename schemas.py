"""
Pydantic v2 Schemas for Candidate Evaluation Platform FastAPI endpoints.
Enforces weight sum validation on RoleProfile creation.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# Auth Schemas
class RecruiterRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    org_name: str


class RecruiterLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RecruiterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    org_name: str
    created_at: datetime


# Role Profile Schemas
class RoleProfileCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    weight_consistency: Decimal = Field(..., ge=0, le=1)
    weight_pr_quality: Decimal = Field(..., ge=0, le=1)
    weight_review_cycles: Decimal = Field(..., ge=0, le=1)
    weight_collaboration: Decimal = Field(..., ge=0, le=1)
    weight_stability: Decimal = Field(..., ge=0, le=1)

    @field_validator("weight_stability")
    def validate_weights_sum(cls, v, values):
        data = values.data
        w_cons = data.get("weight_consistency", Decimal(0))
        w_pr = data.get("weight_pr_quality", Decimal(0))
        w_rev = data.get("weight_review_cycles", Decimal(0))
        w_collab = data.get("weight_collaboration", Decimal(0))
        total = w_cons + w_pr + w_rev + w_collab + v
        if abs(total - Decimal("1.0")) > Decimal("0.001"):
            raise ValueError(f"Scoring weights must sum to 1.0 exactly (Current sum: {total})")
        return v


class RoleProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    weight_consistency: Decimal
    weight_pr_quality: Decimal
    weight_review_cycles: Decimal
    weight_collaboration: Decimal
    weight_stability: Decimal


# Evaluation Schemas
class EvaluationCreateRequest(BaseModel):
    candidate_name: str
    candidate_email: EmailStr
    github_username: str
    repo_owner: str
    repo_name: str
    start_date: datetime
    end_date: datetime
    role_profile_id: Optional[int] = None


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recruiter_id: int
    role_profile_id: Optional[int] = None
    candidate_name: str
    candidate_email: str
    github_username: str
    repo_owner: str
    repo_name: str
    start_date: datetime
    end_date: datetime
    status: str
    final_score: Optional[Decimal] = None
    share_token: Optional[str] = None
    created_at: datetime
    locked_at: Optional[datetime] = None


class ScoreResponse(BaseModel):
    evaluation_id: int
    status: str
    final_score: Optional[float] = None
    is_locked: bool
    metrics: dict
    flagged_notes: List[str] = []


class TimelineItem(BaseModel):
    type: str  # commit, pull_request, review, comment
    id: int
    timestamp: datetime
    author: str
    summary: str
