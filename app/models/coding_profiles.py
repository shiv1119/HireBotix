import uuid
from enum import Enum
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    ForeignKey,
    UniqueConstraint,
    JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from app.models.enums.coding_profiles import SyncStatusEnum

class CodingProfile(Base):
    __tablename__ = "coding_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    platform = Column(String, nullable=False)
    username = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("user_id", "platform", name="unique_user_platform"),
    )
    user = relationship("User", back_populates="coding_profiles")
    stats = relationship(
        "CodingStats",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan"
    )

class CodingStats(Base):
    __tablename__ = "coding_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        Integer,
        ForeignKey("coding_profiles.id"),
        nullable=False,
        unique=True,
        index=True
    )
    total_solved = Column(Integer)
    rating = Column(Integer)
    languages = Column(JSON)
    last_synced = Column(DateTime(timezone=True))
    sync_status = Column(String, default=SyncStatusEnum.PENDING.value)
    updated_at = Column(DateTime(timezone=True, ), onupdate=func.now())
    profile = relationship("CodingProfile", back_populates="stats")
