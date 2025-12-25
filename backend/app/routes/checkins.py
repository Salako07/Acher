from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import pytz
from app.database import get_db
from app.models import User, Project, ProjectMembership, DailyCheckin, CheckinStatus
from app.schemas import CheckinCreate, CheckinResponse
from app.auth import get_current_user


router = APIRouter(prefix="/checkins", tags=["checkins"])


def get_project_current_date(project: Project) -> tuple:
    """
    Get current date in project's timezone.
    Returns (date, datetime) tuple.
    """
    tz = pytz.timezone(project.timezone)
    now = datetime.now(tz)
    return now.date(), now


@router.post("", response_model=CheckinResponse, status_code=status.HTTP_201_CREATED)
async def create_checkin(
    checkin_data: CheckinCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark daily check-in as DONE.

    Rules enforced:
    - User must be a member of the project
    - Only one check-in per user per project per day
    - Cannot check in for past or future dates
    - Check-in is final and immutable
    """

    # Get project
    result = await db.execute(
        select(Project).where(Project.id == checkin_data.project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check if user is a member
    membership_result = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.user_id == current_user.id,
            ProjectMembership.project_id == project.id
        )
    )
    if not membership_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project"
        )

    # Get current date in project timezone
    today, now = get_project_current_date(project)

    # Lock rules after first check-in
    if not project.rules_locked:
        project.rules_locked = True

    # Check if already checked in today
    existing_checkin = await db.execute(
        select(DailyCheckin).where(
            DailyCheckin.user_id == current_user.id,
            DailyCheckin.project_id == project.id,
            DailyCheckin.date == today
        )
    )
    if existing_checkin.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already checked in today"
        )

    # Create check-in
    checkin = DailyCheckin(
        user_id=current_user.id,
        project_id=project.id,
        date=today,
        status=CheckinStatus.DONE,
        checked_at=now,
        auto_marked=False
    )
    db.add(checkin)
    await db.commit()
    await db.refresh(checkin)

    return checkin
