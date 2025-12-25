from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import date, datetime
from typing import List
import pytz
from app.database import get_db
from app.models import User, Project, ProjectMembership, DailyCheckin
from app.schemas import (
    ProjectCreate, ProjectResponse, ProjectDetailResponse,
    ProjectListItem, ProjectMemberResponse, TodayStatus
)
from app.auth import get_current_user


router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_today_date(project: Project) -> date:
    """Get today's date in project's timezone."""
    tz = pytz.timezone(project.timezone)
    now = datetime.now(tz)
    return now.date()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new accountability project."""

    # Validate timezone
    try:
        pytz.timezone(project_data.timezone)
    except pytz.UnknownTimeZoneError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid timezone"
        )

    # Create project
    project = Project(
        name=project_data.name,
        description=project_data.description,
        timezone=project_data.timezone,
        daily_reset_hour=project_data.daily_reset_hour,
        creator_id=current_user.id,
        rules_locked=False
    )
    db.add(project)
    await db.flush()

    # Add creator as member
    membership = ProjectMembership(
        user_id=current_user.id,
        project_id=project.id
    )
    db.add(membership)

    await db.commit()
    await db.refresh(project)

    return project


@router.get("", response_model=List[ProjectListItem])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all projects the user is a member of."""

    # Get user's memberships
    result = await db.execute(
        select(ProjectMembership)
        .where(ProjectMembership.user_id == current_user.id)
        .options(selectinload(ProjectMembership.project))
    )
    memberships = result.scalars().all()

    projects_data = []
    for membership in memberships:
        project = membership.project
        today = get_project_today_date(project)

        # Get member count
        member_count_result = await db.execute(
            select(func.count(ProjectMembership.id))
            .where(ProjectMembership.project_id == project.id)
        )
        member_count = member_count_result.scalar()

        # Get user's status today
        checkin_result = await db.execute(
            select(DailyCheckin)
            .where(
                DailyCheckin.project_id == project.id,
                DailyCheckin.user_id == current_user.id,
                DailyCheckin.date == today
            )
        )
        checkin = checkin_result.scalar_one_or_none()

        projects_data.append(ProjectListItem(
            id=project.id,
            name=project.name,
            description=project.description,
            member_count=member_count,
            user_status_today=checkin.status if checkin else None
        ))

    return projects_data


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed project information including today's status for all members."""

    # Get project
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.memberships).selectinload(ProjectMembership.user))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check if user is a member
    is_member = any(m.user_id == current_user.id for m in project.memberships)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project"
        )

    today = get_project_today_date(project)

    # Get today's check-ins for all members
    checkins_result = await db.execute(
        select(DailyCheckin)
        .where(
            DailyCheckin.project_id == project_id,
            DailyCheckin.date == today
        )
    )
    checkins = {c.user_id: c for c in checkins_result.scalars().all()}

    # Build response
    members = [
        ProjectMemberResponse(
            id=m.user.id,
            username=m.user.username,
            joined_at=m.joined_at
        )
        for m in project.memberships
    ]

    today_statuses = [
        TodayStatus(
            user_id=m.user.id,
            username=m.user.username,
            status=checkins[m.user.id].status if m.user.id in checkins else None,
            checked_at=checkins[m.user.id].checked_at if m.user.id in checkins else None
        )
        for m in project.memberships
    ]

    return ProjectDetailResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        timezone=project.timezone,
        daily_reset_hour=project.daily_reset_hour,
        creator_id=project.creator_id,
        created_at=project.created_at,
        rules_locked=project.rules_locked,
        members=members,
        today_statuses=today_statuses
    )
