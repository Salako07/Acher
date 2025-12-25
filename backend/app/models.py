from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Enum as SQLEnum, Index, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.database import Base


class CheckinStatus(enum.Enum):
    """Status of a daily check-in."""
    DONE = "DONE"
    MISSED = "MISSED"


class User(Base):
    """User account."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    memberships = relationship("ProjectMembership", back_populates="user", cascade="all, delete-orphan")
    checkins = relationship("DailyCheckin", back_populates="user", cascade="all, delete-orphan")
    created_projects = relationship("Project", back_populates="creator", foreign_keys="Project.creator_id")


class Project(Base):
    """Accountability project."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    timezone = Column(String, nullable=False, default="UTC")
    daily_reset_hour = Column(Integer, nullable=False, default=0)  # 0-23
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    rules_locked = Column(Boolean, default=False, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="created_projects", foreign_keys=[creator_id])
    memberships = relationship("ProjectMembership", back_populates="project", cascade="all, delete-orphan")
    invites = relationship("ProjectInvite", back_populates="project", cascade="all, delete-orphan")
    checkins = relationship("DailyCheckin", back_populates="project", cascade="all, delete-orphan")


class ProjectMembership(Base):
    """User membership in a project."""
    __tablename__ = "project_memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="memberships")
    project = relationship("Project", back_populates="memberships")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'project_id', name='unique_user_project'),
        Index('ix_project_memberships_user_project', 'user_id', 'project_id'),
    )


class ProjectInvite(Base):
    """Invitation code for a project."""
    __tablename__ = "project_invites"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    max_uses = Column(Integer, nullable=True)
    current_uses = Column(Integer, default=0, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="invites")


class DailyCheckin(Base):
    """Daily check-in record."""
    __tablename__ = "daily_checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(SQLEnum(CheckinStatus), nullable=False)
    checked_at = Column(DateTime(timezone=True), nullable=True)  # Null for MISSED
    auto_marked = Column(Boolean, default=False, nullable=False)  # True if auto-marked MISSED

    # Relationships
    user = relationship("User", back_populates="checkins")
    project = relationship("Project", back_populates="checkins")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'project_id', 'date', name='unique_user_project_date'),
        Index('ix_checkins_project_date', 'project_id', 'date'),
        Index('ix_checkins_user_project', 'user_id', 'project_id'),
    )
