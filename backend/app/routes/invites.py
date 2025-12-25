from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import secrets
from app.database import get_db
from app.models import User, Project, ProjectMembership, ProjectInvite
from app.schemas import InviteCreate, InviteResponse, InviteAccept
from app.auth import get_current_user


router = APIRouter(prefix="/invites", tags=["invites"])


def generate_invite_code() -> str:
    """Generate a unique invite code."""
    return secrets.token_urlsafe(16)


@router.post("", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    invite_data: InviteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate an invite code for a project."""

    # Get project
    result = await db.execute(
        select(Project).where(Project.id == invite_data.project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check if user is the creator
    if project.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project creator can create invites"
        )

    # Generate unique code
    code = generate_invite_code()
    while True:
        existing = await db.execute(
            select(ProjectInvite).where(ProjectInvite.code == code)
        )
        if not existing.scalar_one_or_none():
            break
        code = generate_invite_code()

    # Calculate expiration
    expires_at = None
    if invite_data.expires_hours:
        expires_at = datetime.utcnow() + timedelta(hours=invite_data.expires_hours)

    # Create invite
    invite = ProjectInvite(
        project_id=invite_data.project_id,
        code=code,
        created_by=current_user.id,
        expires_at=expires_at,
        max_uses=invite_data.max_uses,
        current_uses=0
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)

    return invite


@router.post("/accept", status_code=status.HTTP_200_OK)
async def accept_invite(
    accept_data: InviteAccept,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept an invite and join a project."""

    # Get invite
    result = await db.execute(
        select(ProjectInvite).where(ProjectInvite.code == accept_data.code)
    )
    invite = result.scalar_one_or_none()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite code"
        )

    # Check if expired
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite expired"
        )

    # Check max uses
    if invite.max_uses and invite.current_uses >= invite.max_uses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite max uses reached"
        )

    # Check if already a member
    existing_membership = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.user_id == current_user.id,
            ProjectMembership.project_id == invite.project_id
        )
    )
    if existing_membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this project"
        )

    # Create membership
    membership = ProjectMembership(
        user_id=current_user.id,
        project_id=invite.project_id
    )
    db.add(membership)

    # Increment invite usage
    invite.current_uses += 1

    await db.commit()

    return {"message": "Successfully joined project", "project_id": invite.project_id}
