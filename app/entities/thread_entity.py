from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, func, Index, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import uuid


class ThreadEntity(Base):
    __tablename__ = "threads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    wren_thread_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    chatbot_id: Mapped[int] = mapped_column(
        ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_threads_org_user_last_msg", "org_id", "user_id", "last_message_at"),
        Index(
            "ix_threads_org_chatbot_last_msg", "org_id", "chatbot_id", "last_message_at"
        ),
    )

    organization: Mapped["OrganizationEntity"] = relationship("OrganizationEntity")
    user: Mapped["UserEntity"] = relationship("UserEntity")
    chatbot: Mapped["ChatbotEntity"] = relationship("ChatbotEntity")
    messages: Mapped[list["MessageEntity"]] = relationship(
        "MessageEntity", back_populates="thread", cascade="all, delete-orphan"
    )
    artifacts: Mapped[list["ArtifactEntity"]] = relationship(
        "ArtifactEntity", back_populates="thread", cascade="all, delete-orphan"
    )
