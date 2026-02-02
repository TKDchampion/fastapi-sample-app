from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ReportGroupEntity(Base):
    __tablename__ = "report_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_group_set_id: Mapped[int] = mapped_column(
        ForeignKey("report_group_sets.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    logo: Mapped[str | None] = mapped_column(String, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    report_group_set: Mapped["ReportGroupSetEntity"] = relationship("ReportGroupSetEntity", back_populates="report_groups")
    reports: Mapped[list["ReportEntity"]] = relationship("ReportEntity", back_populates="group", passive_deletes=True)
