"""Pydantic schemas used by the FastAPI service."""
from __future__ import annotations

from datetime import datetime, date
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------- Auth & Users ----------


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class LogoutRequest(BaseModel):
    token: str


class RefreshRequest(BaseModel):
    token: str


class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    role: str = "analyst"


class UserCreate(UserBase):
    password: str = Field(..., min_length=4)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None


class UserResponse(UserBase):
    id: str
    created_at: datetime


class RoleUpdateRequest(BaseModel):
    role: str


# ---------- Sources ----------


class SourceBase(BaseModel):
    name: str
    type: str
    config: Dict[str, object]
    status: str = "inactive"
    schedule: str = "manual"


class SourceResponse(SourceBase):
    id: str
    last_run: Optional[datetime] = None
    last_error: Optional[str] = None


class SourceStatusResponse(BaseModel):
    sources: List[SourceResponse]
    last_updated: datetime


# ---------- Contents & Sentiment ----------


class SentimentSummary(BaseModel):
    label: Optional[str] = None
    score: Optional[float] = None
    scores_by_label: Optional[Dict[str, float]] = None
    scored_at: Optional[datetime] = None


class SentimentHistory(BaseModel):
    label: str
    score: float
    scored_at: datetime
    model_name: str
    model_version: str


class ContentResponse(BaseModel):
    id: UUID
    source_type: str
    source_id: str
    title: Optional[str]
    body: str
    language: str
    published_at: Optional[datetime]
    ingested_at: datetime
    labels: Optional[List[str]] = None
    sentiment: Optional[SentimentSummary] = None


class ContentExportResponse(BaseModel):
    filename: str
    generated_at: datetime


class LabelUpdateRequest(BaseModel):
    label: str


class SentimentAnalyzeRequest(BaseModel):
    text: str


class SentimentAnalyzeResponse(BaseModel):
    sentiment: str
    score: float
    scores_by_label: Dict[str, float]
    created_at: datetime


class SentimentStatsResponse(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    total: int = 0
    updated_at: datetime


class SentimentTrendPoint(BaseModel):
    date: date
    positive: int
    neutral: int
    negative: int


class KeywordResponse(BaseModel):
    keyword: str
    count: int


class BrandSentimentResponse(BaseModel):
    label: str
    positive: int
    neutral: int
    negative: int
    total: int
    top_items: list[ContentResponse]


class RetrainRequest(BaseModel):
    dataset_version: str
    notes: Optional[str] = None


class RetrainResponse(BaseModel):
    job_id: str
    status: str
    submitted_at: datetime


class SentimentAccuracyResponse(BaseModel):
    model_name: str
    model_version: str
    accuracy: float
    evaluated_at: datetime


class KeywordSentimentStats(BaseModel):
    keyword: str
    positive: int
    neutral: int
    negative: int
    total: int
    updated_at: datetime


# ---------- Reports ----------


class ReportGenerateRequest(BaseModel):
    type: str = "pdf"
    date_range: Dict[str, str]
    include_charts: bool = True


class ReportResponse(BaseModel):
    id: str
    status: str
    generated_at: datetime
    download_url: Optional[str] = None


# ---------- Branding ----------


class BrandingConfig(BaseModel):
    organization: str
    primary_color: str
    logo_url: str


class BrandingTemplate(BaseModel):
    header: str
    footer: str


class BrandingUpdateRequest(BaseModel):
    organization: Optional[str] = None
    primary_color: Optional[str] = None
    logo_url: Optional[str] = None


class BrandingTemplateUpdate(BaseModel):
    header: Optional[str] = None
    footer: Optional[str] = None


# ---------- System ----------


class SystemStatusResponse(BaseModel):
    status: str
    ingested_items: int
    pending_sentiments: int
    timestamp: datetime


class SystemLogsResponse(BaseModel):
    logs: List[dict]


class BackupResponse(BaseModel):
    status: str
    started_at: datetime


class VersionResponse(BaseModel):
    api_version: str
    model_version: str
    git_sha: str


# ---------- Security ----------


class AuditLogResponse(BaseModel):
    id: str
    action: str
    message: str
    timestamp: datetime


class AuditSearchRequest(BaseModel):
    user: Optional[str] = None
    action: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class RoleResponse(BaseModel):
    id: str
    name: str
    permissions: List[str]


class RolePermissionsUpdate(BaseModel):
    permissions: List[str]
