from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, func, Index, UUID, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import uuid
import enum


class ArtifactType(str, enum.Enum):
    chart = "chart"
    table = "table"
    image = "image"
    file = "file"
    code = "code"
    json_schema = "json_schema"


class ArtifactEntity(Base):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[ArtifactType] = mapped_column(SAEnum(ArtifactType), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    spec_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    data_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    storage_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_artifacts_thread_created_at", "thread_id", "created_at"),
        Index("ix_artifacts_message_id", "message_id"),
    )

    thread: Mapped["ThreadEntity"] = relationship("ThreadEntity", back_populates="artifacts")
    message: Mapped["MessageEntity"] = relationship("MessageEntity", back_populates="artifacts")
