from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, BigInteger, Text, DateTime, ForeignKey, func, Index, UUID, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import uuid
import enum


class MessageRole(str, enum.Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"


class MessageContentType(str, enum.Enum):
    text = "text"
    markdown = "markdown"
    json = "json"
    tool_call = "tool_call"
    tool_result = "tool_result"
    image_ref = "image_ref"
    error = "error"


class MessageStatus(str, enum.Enum):
    final = "final"
    streaming = "streaming"
    failed = "failed"
    cancelled = "cancelled"


class MessageEntity(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False
    )
    seq: Mapped[int] = mapped_column(BigInteger, nullable=False)
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole), nullable=False)
    content_type: Mapped[MessageContentType] = mapped_column(SAEnum(MessageContentType), nullable=False)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[MessageStatus] = mapped_column(SAEnum(MessageStatus), nullable=False, default=MessageStatus.final)
    parent_message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_messages_thread_seq", "thread_id", "seq"),
        Index("ix_messages_thread_created_at", "thread_id", "created_at"),
    )

    thread: Mapped["ThreadEntity"] = relationship("ThreadEntity", back_populates="messages")
    artifacts: Mapped[list["ArtifactEntity"]] = relationship("ArtifactEntity", back_populates="message")
