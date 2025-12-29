from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserReportGroupSetAccessEntity(Base):
    __tablename__ = "user_report_group_set_accesses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    report_group_set_id: Mapped[int] = mapped_column(
        ForeignKey("report_group_sets.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    user: Mapped["UserEntity"] = relationship("UserEntity", back_populates="report_group_set_accesses")
    report_group_set: Mapped["ReportGroupSetEntity"] = relationship("ReportGroupSetEntity", back_populates="user_accesses")
