from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, date
import pytz
import logging
from app.database import AsyncSessionLocal
from app.models import Project, ProjectMembership, DailyCheckin, CheckinStatus


logger = logging.getLogger(__name__)


async def auto_mark_missed_days():
    """
    Background task to auto-mark missed check-ins.

    This runs every hour and checks all projects to see if their day has ended.
    For projects where the day has ended, it marks all non-checked users as MISSED.

    Idempotent: Safe to run multiple times.
    """
    logger.info("Running auto-mark missed days task")

    async with AsyncSessionLocal() as db:
        try:
            # Get all projects
            result = await db.execute(select(Project))
            projects = result.scalars().all()

            for project in projects:
                await process_project_missed_checkins(db, project)

            await db.commit()
            logger.info("Auto-mark missed days task completed")

        except Exception as e:
            logger.error(f"Error in auto-mark missed days: {e}")
            await db.rollback()


async def process_project_missed_checkins(db: AsyncSession, project: Project):
    """
    Process a single project to mark missed check-ins.

    Logic:
    1. Determine if the previous day has ended based on reset hour
    2. Find all members who didn't check in for that day
    3. Create MISSED records for them
    """
    try:
        # Get project timezone
        tz = pytz.timezone(project.timezone)
        now = datetime.now(tz)

        # Check if we've passed the reset hour today
        reset_time_today = now.replace(hour=project.daily_reset_hour, minute=0, second=0, microsecond=0)

        # If we haven't passed the reset hour yet, yesterday is still active - skip
        if now < reset_time_today:
            return

        # Get yesterday's date (the day that just ended at reset hour)
        yesterday = (now - timedelta(days=1)).date()

        # Get all members
        members_result = await db.execute(
            select(ProjectMembership).where(
                ProjectMembership.project_id == project.id
            )
        )
        members = members_result.scalars().all()

        for member in members:
            # Only mark as missed if user was a member on that day
            join_date = member.joined_at.date()
            if join_date > yesterday:
                continue

            # Check if already has a check-in for yesterday
            existing = await db.execute(
                select(DailyCheckin).where(
                    DailyCheckin.user_id == member.user_id,
                    DailyCheckin.project_id == project.id,
                    DailyCheckin.date == yesterday
                )
            )

            if not existing.scalar_one_or_none():
                # Create MISSED record
                missed_checkin = DailyCheckin(
                    user_id=member.user_id,
                    project_id=project.id,
                    date=yesterday,
                    status=CheckinStatus.MISSED,
                    checked_at=None,
                    auto_marked=True
                )
                db.add(missed_checkin)
                logger.info(
                    f"Marked user {member.user_id} as MISSED "
                    f"for project {project.id} on {yesterday}"
                )

    except Exception as e:
        logger.error(f"Error processing project {project.id}: {e}")


def start_scheduler():
    """Initialize and start the background scheduler."""
    scheduler = AsyncIOScheduler()

    # Run every hour at minute 0
    # This ensures we catch missed days across all timezones
    scheduler.add_job(
        auto_mark_missed_days,
        CronTrigger(minute=0),
        id="auto_mark_missed",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started")

    return scheduler
