from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import date, timedelta
from app.database import get_db
from app.models import User, Project, ProjectMembership, DailyCheckin, CheckinStatus
from app.schemas import ProjectAnalytics, UserStreak, UserAnalytics, CheckinResponse
from app.auth import get_current_user


router = APIRouter(prefix="/analytics", tags=["analytics"])


def calculate_streak(checkins: list[DailyCheckin], until_date: date) -> tuple:
    """
    Calculate current and longest streak from checkins.
    Returns (current_streak, longest_streak).

    Current streak: Consecutive DONE days counting backward from until_date.
    If no check-in exists for until_date, starts counting from until_date - 1.
    This allows streaks to persist throughout the current day before check-in.
    """
    if not checkins:
        return 0, 0

    # Sort by date descending
    sorted_checkins = sorted(
        [c for c in checkins if c.status == CheckinStatus.DONE],
        key=lambda x: x.date,
        reverse=True
    )

    if not sorted_checkins:
        return 0, 0

    # Calculate current streak
    current_streak = 0
    check_date = until_date

    # If no check-in today, start counting from yesterday
    # This allows a streak to persist throughout today before check-in
    if sorted_checkins[0].date != until_date:
        check_date = until_date - timedelta(days=1)

    for checkin in sorted_checkins:
        if checkin.date == check_date:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Calculate longest streak
    longest_streak = 0
    temp_streak = 0
    prev_date = None

    for checkin in sorted(sorted_checkins, key=lambda x: x.date):
        if prev_date is None or checkin.date == prev_date + timedelta(days=1):
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 1

        prev_date = checkin.date

    return current_streak, longest_streak


@router.get("/projects/{project_id}", response_model=ProjectAnalytics)
async def get_project_analytics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics for a project including all members' streaks."""

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

    # Get all check-ins for the project
    checkins_result = await db.execute(
        select(DailyCheckin).where(DailyCheckin.project_id == project_id)
    )
    all_checkins = checkins_result.scalars().all()

    # Group by user
    user_checkins = {}
    for checkin in all_checkins:
        if checkin.user_id not in user_checkins:
            user_checkins[checkin.user_id] = []
        user_checkins[checkin.user_id].append(checkin)

    # Calculate project age in days
    today = date.today()
    project_start_date = project.created_at.date()
    total_project_days = (today - project_start_date).days + 1

    # Build user streaks
    user_streaks = []
    for membership in project.memberships:
        user = membership.user
        checkins = user_checkins.get(user.id, [])

        # Calculate days since user joined
        join_date = membership.joined_at.date()
        total_days = (today - join_date).days + 1

        current_streak, longest_streak = calculate_streak(checkins, today)
        total_checkins = len([c for c in checkins if c.status == CheckinStatus.DONE])

        consistency_percent = (total_checkins / total_days * 100) if total_days > 0 else 0

        user_streaks.append(UserStreak(
            user_id=user.id,
            username=user.username,
            current_streak=current_streak,
            longest_streak=longest_streak,
            total_checkins=total_checkins,
            total_days=total_days,
            consistency_percent=round(consistency_percent, 1)
        ))

    return ProjectAnalytics(
        project_id=project.id,
        project_name=project.name,
        user_streaks=user_streaks,
        total_project_days=total_project_days
    )


@router.get("/users/{user_id}/projects/{project_id}", response_model=UserAnalytics)
async def get_user_analytics(
    user_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed analytics for a specific user in a project."""

    # Get project
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check if current user is a member
    is_member = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.user_id == current_user.id,
            ProjectMembership.project_id == project_id
        )
    )
    if not is_member.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project"
        )

    # Get target user
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get user's membership
    membership_result = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.user_id == user_id,
            ProjectMembership.project_id == project_id
        )
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this project"
        )

    # Get user's check-ins
    checkins_result = await db.execute(
        select(DailyCheckin)
        .where(
            DailyCheckin.user_id == user_id,
            DailyCheckin.project_id == project_id
        )
        .order_by(DailyCheckin.date.desc())
    )
    checkins = checkins_result.scalars().all()

    # Calculate stats
    today = date.today()
    join_date = membership.joined_at.date()
    total_days = (today - join_date).days + 1

    current_streak, longest_streak = calculate_streak(checkins, today)
    total_checkins = len([c for c in checkins if c.status == CheckinStatus.DONE])
    consistency_percent = (total_checkins / total_days * 100) if total_days > 0 else 0

    return UserAnalytics(
        user_id=user.id,
        username=user.username,
        project_id=project.id,
        checkins=[CheckinResponse.model_validate(c) for c in checkins],
        current_streak=current_streak,
        longest_streak=longest_streak,
        consistency_percent=round(consistency_percent, 1)
    )
