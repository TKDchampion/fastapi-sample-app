from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, func, Index, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class OrgUserChatbotEntity(Base):
    __tablename__ = "org_user_chatbot"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    chatbot_id: Mapped[int] = mapped_column(
        ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (
        Index(
            "ix_org_user_chatbot_org_user_last", "org_id", "user_id", "last_message_at"
        ),
        Index("ix_org_user_chatbot_chatbot_id", "chatbot_id"),
    )

    organization: Mapped["OrganizationEntity"] = relationship(
        "OrganizationEntity", back_populates="chatbot_conversations"
    )
    user: Mapped["UserEntity"] = relationship(
        "UserEntity", back_populates="chatbot_conversations"
    )
    chatbot: Mapped["ChatbotEntity"] = relationship(
        "ChatbotEntity", back_populates="conversations"
    )
