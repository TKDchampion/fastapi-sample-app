from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ChatbotCsvEntity(Base):
    __tablename__ = "chatbot_csvs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chatbot_id: Mapped[int] = mapped_column(
        ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False
    )
    gcs_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (Index("ix_chatbot_csvs_chatbot_id", "chatbot_id"),)
