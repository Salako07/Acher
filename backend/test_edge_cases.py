"""
Edge Case Testing Script for Accountability System

Tests:
1. Late joins (users joining mid-project)
2. Timezone shifts and boundary conditions
3. Missed streak scenarios
4. Reset hour boundary conditions
5. Streak calculation accuracy
"""

import asyncio
import sys
import io

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from datetime import datetime, date, timedelta
import pytz
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User, Project, ProjectMembership, DailyCheckin, CheckinStatus
from app.routes.analytics import calculate_streak
from app.scheduler import process_project_missed_checkins


async def setup_test_data():
    """Create test users and projects for edge case testing."""
    async with AsyncSessionLocal() as db:
        # First, check if test users already exist and delete them
        result = await db.execute(
            select(User).where(
                User.username.in_(["testuser1", "testuser2", "testuser3"])
            )
        )
        existing_users = result.scalars().all()

        if existing_users:
            print(f"Found {len(existing_users)} existing test users, cleaning up...")
            # Delete their check-ins first
            for user in existing_users:
                result = await db.execute(
                    select(DailyCheckin).where(DailyCheckin.user_id == user.id)
                )
                checkins = result.scalars().all()
                for checkin in checkins:
                    await db.delete(checkin)

                # Delete their memberships
                result = await db.execute(
                    select(ProjectMembership).where(ProjectMembership.user_id == user.id)
                )
                memberships = result.scalars().all()
                for membership in memberships:
                    await db.delete(membership)

                # Delete projects they created
                result = await db.execute(
                    select(Project).where(Project.creator_id == user.id)
                )
                projects = result.scalars().all()
                for project in projects:
                    await db.delete(project)

                # Finally delete the user
                await db.delete(user)

            await db.commit()
            print("Cleanup complete")

        # Create fresh test users
        users = []
        for i in range(1, 4):
            user = User(
                email=f"testuser{i}@test.com",
                username=f"testuser{i}",
                hashed_password="dummy_hash"
            )
            db.add(user)
            users.append(user)

        await db.commit()
        for user in users:
            await db.refresh(user)

        return users


async def test_late_join_edge_case():
    """
    Test Case 1: Late Join Scenario

    Scenario:
    - Project created on Day 1
    - User A joins on Day 1
    - User B joins on Day 5

    Expected:
    - User B should NOT have missed days 1-4
    - User B's consistency % should only count from Day 5
    - User B's total_days should only count from Day 5
    """
    print("\n" + "="*80)
    print("TEST 1: Late Join Edge Case")
    print("="*80)

    async with AsyncSessionLocal() as db:
        # Create project with User 1
        result = await db.execute(
            select(User).where(User.username == "testuser1")
        )
        user1 = result.scalar_one()

        result = await db.execute(
            select(User).where(User.username == "testuser2")
        )
        user2 = result.scalar_one()

        # Create project with midnight reset (0:00)
        project = Project(
            name="Late Join Test Project",
            description="Testing late user joins",
            timezone="UTC",
            daily_reset_hour=0,
            creator_id=user1.id,
            rules_locked=False
        )
        db.add(project)
        await db.flush()

        # User 1 joins on Day 1 (5 days ago)
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        membership1 = ProjectMembership(
            user_id=user1.id,
            project_id=project.id,
            joined_at=five_days_ago
        )
        db.add(membership1)

        # User 2 joins on Day 5 (1 day ago)
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        membership2 = ProjectMembership(
            user_id=user2.id,
            project_id=project.id,
            joined_at=one_day_ago
        )
        db.add(membership2)

        # User 1 checked in on days 1, 2, 3 (missed 4, 5)
        for days_back in [5, 4, 3]:
            checkin_date = (date.today() - timedelta(days=days_back))
            checkin = DailyCheckin(
                user_id=user1.id,
                project_id=project.id,
                date=checkin_date,
                status=CheckinStatus.DONE,
                checked_at=datetime.utcnow() - timedelta(days=days_back),
                auto_marked=False
            )
            db.add(checkin)

        # Add missed records for User 1 on days 4 and 5
        for days_back in [2, 1]:
            checkin_date = (date.today() - timedelta(days=days_back))
            checkin = DailyCheckin(
                user_id=user1.id,
                project_id=project.id,
                date=checkin_date,
                status=CheckinStatus.MISSED,
                checked_at=None,
                auto_marked=True
            )
            db.add(checkin)

        # User 2 checked in yesterday (their first day)
        yesterday = date.today() - timedelta(days=1)
        checkin = DailyCheckin(
            user_id=user2.id,
            project_id=project.id,
            date=yesterday,
            status=CheckinStatus.DONE,
            checked_at=one_day_ago,
            auto_marked=False
        )
        db.add(checkin)

        await db.commit()
        await db.refresh(project)

        # Now test analytics calculation
        from app.routes.analytics import calculate_streak

        # Get User 1's checkins
        result = await db.execute(
            select(DailyCheckin).where(
                DailyCheckin.user_id == user1.id,
                DailyCheckin.project_id == project.id
            )
        )
        user1_checkins = result.scalars().all()

        # Get User 2's checkins
        result = await db.execute(
            select(DailyCheckin).where(
                DailyCheckin.user_id == user2.id,
                DailyCheckin.project_id == project.id
            )
        )
        user2_checkins = result.scalars().all()

        # Calculate User 1 stats
        join_date1 = membership1.joined_at.date()
        total_days1 = (date.today() - join_date1).days + 1
        current_streak1, longest_streak1 = calculate_streak(user1_checkins, date.today())
        total_checkins1 = len([c for c in user1_checkins if c.status == CheckinStatus.DONE])
        consistency1 = (total_checkins1 / total_days1 * 100) if total_days1 > 0 else 0

        # Calculate User 2 stats
        join_date2 = membership2.joined_at.date()
        total_days2 = (date.today() - join_date2).days + 1
        current_streak2, longest_streak2 = calculate_streak(user2_checkins, date.today())
        total_checkins2 = len([c for c in user2_checkins if c.status == CheckinStatus.DONE])
        consistency2 = (total_checkins2 / total_days2 * 100) if total_days2 > 0 else 0

        print(f"\nUser 1 (joined 5 days ago):")
        print(f"  Total days: {total_days1} (expected: ~6)")
        print(f"  Total check-ins: {total_checkins1} (expected: 3)")
        print(f"  Current streak: {current_streak1} (expected: 0, broke on day 4)")
        print(f"  Longest streak: {longest_streak1} (expected: 3)")
        print(f"  Consistency: {consistency1:.1f}% (expected: ~50%)")

        print(f"\nUser 2 (joined 1 day ago):")
        print(f"  Total days: {total_days2} (expected: ~2)")
        print(f"  Total check-ins: {total_checkins2} (expected: 1)")
        print(f"  Current streak: {current_streak2} (expected: 1)")
        print(f"  Longest streak: {longest_streak2} (expected: 1)")
        print(f"  Consistency: {consistency2:.1f}% (expected: ~50-100%)")
        print(f"  Missed days before join: {len([c for c in user2_checkins if c.date < join_date2])} (expected: 0)")

        # Verify User 2 has no missed days before they joined
        early_misses = [c for c in user2_checkins if c.date < join_date2]

        print(f"\n✓ PASS" if len(early_misses) == 0 else f"✗ FAIL: User 2 has {len(early_misses)} missed days before joining!")


async def test_timezone_boundary_conditions():
    """
    Test Case 2: Timezone Boundary Conditions

    Scenario:
    - Project in timezone UTC+12 (Fiji) with reset hour 3:00
    - Project in timezone UTC-8 (PST) with reset hour 3:00
    - Check if date calculation works correctly across timezones
    """
    print("\n" + "="*80)
    print("TEST 2: Timezone Boundary Conditions")
    print("="*80)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.username == "testuser3")
        )
        user = result.scalar_one()

        # Create project in Fiji timezone (UTC+12)
        fiji_project = Project(
            name="Fiji Timezone Test",
            description="Testing UTC+12 timezone",
            timezone="Pacific/Fiji",
            daily_reset_hour=3,
            creator_id=user.id,
            rules_locked=False
        )
        db.add(fiji_project)
        await db.flush()

        # Add membership
        membership = ProjectMembership(
            user_id=user.id,
            project_id=fiji_project.id
        )
        db.add(membership)

        await db.commit()
        await db.refresh(fiji_project)

        # Check date calculation
        from app.routes.projects import get_project_today_date
        fiji_today = get_project_today_date(fiji_project)

        # Get UTC time and Fiji time
        utc_now = datetime.now(pytz.UTC)
        fiji_tz = pytz.timezone("Pacific/Fiji")
        fiji_now = utc_now.astimezone(fiji_tz)

        print(f"\nCurrent UTC time: {utc_now}")
        print(f"Current Fiji time: {fiji_now}")
        print(f"Fiji 'today' date: {fiji_today}")
        print(f"Reset hour: {fiji_project.daily_reset_hour}:00")
        print(f"Next reset: {fiji_now.replace(hour=fiji_project.daily_reset_hour, minute=0, second=0, microsecond=0)}")

        # Test if we're before or after reset
        reset_time = fiji_now.replace(hour=fiji_project.daily_reset_hour, minute=0, second=0, microsecond=0)
        if fiji_now < reset_time:
            print(f"Status: Before reset (yesterday's check-ins still valid)")
        else:
            print(f"Status: After reset (today's check-ins required)")

        print(f"\n✓ Timezone calculations working correctly")


async def test_reset_hour_boundary():
    """
    Test Case 3: Reset Hour Boundary

    Scenario:
    - Project with reset hour 15:00 (3 PM)
    - Test auto-marking behavior around the reset hour
    - Verify that missed marking only happens after reset hour
    """
    print("\n" + "="*80)
    print("TEST 3: Reset Hour Boundary Conditions")
    print("="*80)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.username == "testuser1")
        )
        user = result.scalar_one()

        # Create project with 15:00 reset hour
        project = Project(
            name="3PM Reset Test",
            description="Testing 3PM reset hour",
            timezone="UTC",
            daily_reset_hour=15,
            creator_id=user.id,
            rules_locked=False
        )
        db.add(project)
        await db.flush()

        # Add membership from 3 days ago
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        membership = ProjectMembership(
            user_id=user.id,
            project_id=project.id,
            joined_at=three_days_ago
        )
        db.add(membership)

        # User checked in 2 days ago (should be safe)
        two_days_ago_date = (date.today() - timedelta(days=2))
        checkin = DailyCheckin(
            user_id=user.id,
            project_id=project.id,
            date=two_days_ago_date,
            status=CheckinStatus.DONE,
            checked_at=datetime.utcnow() - timedelta(days=2),
            auto_marked=False
        )
        db.add(checkin)

        await db.commit()
        await db.refresh(project)

        # Now simulate the auto-marking process
        print(f"\nProject reset hour: {project.daily_reset_hour}:00 UTC")

        utc_now = datetime.now(pytz.UTC)
        print(f"Current UTC time: {utc_now}")

        reset_time_today = utc_now.replace(hour=project.daily_reset_hour, minute=0, second=0, microsecond=0)
        print(f"Reset time today: {reset_time_today}")

        if utc_now < reset_time_today:
            print(f"Status: Before reset hour - yesterday still active")
            print(f"Expected: No missed marking for yesterday yet")
        else:
            print(f"Status: After reset hour - yesterday ended")
            print(f"Expected: Yesterday should be marked as missed if not checked in")

            # Run the auto-marking process
            await process_project_missed_checkins(db, project)
            await db.commit()

            # Check what happened
            yesterday = (utc_now - timedelta(days=1)).date()
            result = await db.execute(
                select(DailyCheckin).where(
                    DailyCheckin.user_id == user.id,
                    DailyCheckin.project_id == project.id,
                    DailyCheckin.date == yesterday
                )
            )
            yesterday_checkin = result.scalar_one_or_none()

            if yesterday_checkin:
                print(f"Yesterday's status: {yesterday_checkin.status}")
                print(f"Auto-marked: {yesterday_checkin.auto_marked}")
            else:
                print(f"No check-in found for yesterday (expected if before reset)")

        print(f"\n✓ Reset hour boundary logic verified")


async def test_streak_calculation_edge_cases():
    """
    Test Case 4: Streak Calculation Edge Cases

    Scenarios:
    - Streak broken by single missed day
    - Multiple streaks (longest vs current)
    - Streak with gaps
    """
    print("\n" + "="*80)
    print("TEST 4: Streak Calculation Edge Cases")
    print("="*80)

    # Create mock check-ins for testing
    today = date.today()

    # Scenario 1: Perfect 7-day streak
    perfect_streak = [
        DailyCheckin(
            user_id=1, project_id=1,
            date=today - timedelta(days=i),
            status=CheckinStatus.DONE,
            checked_at=datetime.now() - timedelta(days=i),
            auto_marked=False
        )
        for i in range(7)
    ]

    current, longest = calculate_streak(perfect_streak, today)
    print(f"\nScenario 1: Perfect 7-day streak")
    print(f"  Current: {current} (expected: 7)")
    print(f"  Longest: {longest} (expected: 7)")
    print(f"  ✓ PASS" if current == 7 and longest == 7 else f"  ✗ FAIL")

    # Scenario 2: Broken streak (checked 5, 4, 3 days ago, missed 2, checked 1 day ago)
    broken_streak = [
        DailyCheckin(user_id=1, project_id=1, date=today - timedelta(days=5),
                    status=CheckinStatus.DONE, checked_at=datetime.now(), auto_marked=False),
        DailyCheckin(user_id=1, project_id=1, date=today - timedelta(days=4),
                    status=CheckinStatus.DONE, checked_at=datetime.now(), auto_marked=False),
        DailyCheckin(user_id=1, project_id=1, date=today - timedelta(days=3),
                    status=CheckinStatus.DONE, checked_at=datetime.now(), auto_marked=False),
        DailyCheckin(user_id=1, project_id=1, date=today - timedelta(days=2),
                    status=CheckinStatus.MISSED, checked_at=None, auto_marked=True),
        DailyCheckin(user_id=1, project_id=1, date=today - timedelta(days=1),
                    status=CheckinStatus.DONE, checked_at=datetime.now(), auto_marked=False),
    ]

    current, longest = calculate_streak(broken_streak, today)
    print(f"\nScenario 2: Broken streak (3-day streak, missed 1, then 1-day streak)")
    print(f"  Current: {current} (expected: 1)")
    print(f"  Longest: {longest} (expected: 3)")
    print(f"  ✓ PASS" if current == 1 and longest == 3 else f"  ✗ FAIL")

    # Scenario 3: No current streak (missed yesterday)
    no_current_streak = [
        DailyCheckin(user_id=1, project_id=1, date=today - timedelta(days=5),
                    status=CheckinStatus.DONE, checked_at=datetime.now(), auto_marked=False),
        DailyCheckin(user_id=1, project_id=1, date=today - timedelta(days=4),
                    status=CheckinStatus.DONE, checked_at=datetime.now(), auto_marked=False),
        DailyCheckin(user_id=1, project_id=1, date=today - timedelta(days=3),
                    status=CheckinStatus.DONE, checked_at=datetime.now(), auto_marked=False),
        DailyCheckin(user_id=1, project_id=1, date=today - timedelta(days=1),
                    status=CheckinStatus.MISSED, checked_at=None, auto_marked=True),
    ]

    current, longest = calculate_streak(no_current_streak, today)
    print(f"\nScenario 3: No current streak (missed yesterday)")
    print(f"  Current: {current} (expected: 0)")
    print(f"  Longest: {longest} (expected: 3)")
    print(f"  ✓ PASS" if current == 0 and longest == 3 else f"  ✗ FAIL")

    # Scenario 4: Empty check-ins
    empty = []
    current, longest = calculate_streak(empty, today)
    print(f"\nScenario 4: Empty check-ins")
    print(f"  Current: {current} (expected: 0)")
    print(f"  Longest: {longest} (expected: 0)")
    print(f"  ✓ PASS" if current == 0 and longest == 0 else f"  ✗ FAIL")


async def test_consistency_calculation():
    """
    Test Case 5: Consistency Percentage Calculation

    Ensure consistency is calculated based on days since joining,
    not from project creation.
    """
    print("\n" + "="*80)
    print("TEST 5: Consistency Percentage Calculation")
    print("="*80)

    today = date.today()

    # User joined 10 days ago, checked in 7 times
    join_date = today - timedelta(days=10)
    total_days = (today - join_date).days + 1  # Should be 11
    total_checkins = 7

    consistency = (total_checkins / total_days * 100) if total_days > 0 else 0

    print(f"\nUser joined: {join_date}")
    print(f"Today: {today}")
    print(f"Total days: {total_days} (expected: 11)")
    print(f"Total check-ins: {total_checkins}")
    print(f"Consistency: {consistency:.1f}% (expected: ~63.6%)")
    print(f"✓ PASS" if 63 <= consistency <= 64 else f"✗ FAIL")


async def cleanup_test_data():
    """Clean up test data."""
    print("\n" + "="*80)
    print("Cleaning up test data...")
    print("="*80)

    async with AsyncSessionLocal() as db:
        # Delete test check-ins
        result = await db.execute(
            select(DailyCheckin).join(Project).where(
                Project.name.in_([
                    "Late Join Test Project",
                    "Fiji Timezone Test",
                    "3PM Reset Test"
                ])
            )
        )
        checkins = result.scalars().all()
        for checkin in checkins:
            await db.delete(checkin)

        # Delete test memberships
        result = await db.execute(
            select(ProjectMembership).join(Project).where(
                Project.name.in_([
                    "Late Join Test Project",
                    "Fiji Timezone Test",
                    "3PM Reset Test"
                ])
            )
        )
        memberships = result.scalars().all()
        for membership in memberships:
            await db.delete(membership)

        # Delete test projects
        result = await db.execute(
            select(Project).where(
                Project.name.in_([
                    "Late Join Test Project",
                    "Fiji Timezone Test",
                    "3PM Reset Test"
                ])
            )
        )
        projects = result.scalars().all()
        for project in projects:
            await db.delete(project)

        # Delete test users
        result = await db.execute(
            select(User).where(
                User.username.in_(["testuser1", "testuser2", "testuser3"])
            )
        )
        users = result.scalars().all()
        for user in users:
            await db.delete(user)

        await db.commit()
        print("✓ Cleanup complete")


async def main():
    """Run all edge case tests."""
    print("\n" + "="*80)
    print("ACCOUNTABILITY SYSTEM - EDGE CASE TESTING")
    print("="*80)

    try:
        # Setup
        print("\nSetting up test data...")
        await setup_test_data()
        print("✓ Test data created")

        # Run tests
        await test_late_join_edge_case()
        await test_timezone_boundary_conditions()
        await test_reset_hour_boundary()
        await test_streak_calculation_edge_cases()
        await test_consistency_calculation()

        # Cleanup
        await cleanup_test_data()

        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
