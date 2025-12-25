from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime, date
from typing import Optional
from app.models import CheckinStatus


# ============================================================================
# User Schemas
# ============================================================================

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    username: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh."""
    refresh_token: str


# ============================================================================
# Project Schemas
# ============================================================================

class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    timezone: str = Field(default="UTC")
    daily_reset_hour: int = Field(default=0, ge=0, le=23)


class ProjectResponse(BaseModel):
    """Schema for project response."""
    id: int
    name: str
    description: Optional[str]
    timezone: str
    daily_reset_hour: int
    creator_id: int
    created_at: datetime
    rules_locked: bool

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberResponse(BaseModel):
    """Schema for project member."""
    id: int
    username: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TodayStatus(BaseModel):
    """Today's status for a user in a project."""
    user_id: int
    username: str
    status: Optional[CheckinStatus]
    checked_at: Optional[datetime]


class ProjectDetailResponse(BaseModel):
    """Schema for detailed project view."""
    id: int
    name: str
    description: Optional[str]
    timezone: str
    daily_reset_hour: int
    creator_id: int
    created_at: datetime
    rules_locked: bool
    members: list[ProjectMemberResponse]
    today_statuses: list[TodayStatus]

    model_config = ConfigDict(from_attributes=True)


class ProjectListItem(BaseModel):
    """Schema for project list item."""
    id: int
    name: str
    description: Optional[str]
    member_count: int
    user_status_today: Optional[CheckinStatus]


# ============================================================================
# Invite Schemas
# ============================================================================

class InviteCreate(BaseModel):
    """Schema for creating an invite."""
    project_id: int
    max_uses: Optional[int] = None
    expires_hours: Optional[int] = None


class InviteResponse(BaseModel):
    """Schema for invite response."""
    id: int
    project_id: int
    code: str
    created_at: datetime
    expires_at: Optional[datetime]
    max_uses: Optional[int]
    current_uses: int

    model_config = ConfigDict(from_attributes=True)


class InviteAccept(BaseModel):
    """Schema for accepting an invite."""
    code: str


# ============================================================================
# Check-in Schemas
# ============================================================================

class CheckinCreate(BaseModel):
    """Schema for creating a check-in."""
    project_id: int


class CheckinResponse(BaseModel):
    """Schema for check-in response."""
    id: int
    user_id: int
    project_id: int
    date: date
    status: CheckinStatus
    checked_at: Optional[datetime]
    auto_marked: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Analytics Schemas
# ============================================================================

class UserStreak(BaseModel):
    """User streak information."""
    user_id: int
    username: str
    current_streak: int
    longest_streak: int
    total_checkins: int
    total_days: int
    consistency_percent: float


class ProjectAnalytics(BaseModel):
    """Project analytics."""
    project_id: int
    project_name: str
    user_streaks: list[UserStreak]
    total_project_days: int


class UserAnalytics(BaseModel):
    """User analytics for a specific project."""
    user_id: int
    username: str
    project_id: int
    checkins: list[CheckinResponse]
    current_streak: int
    longest_streak: int
    consistency_percent: float
