from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ReportGroupSetEntity(Base):
    __tablename__ = "report_group_sets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
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

    org: Mapped["OrganizationEntity"] = relationship("OrganizationEntity", back_populates="report_group_sets")
    report_groups: Mapped[list["ReportGroupEntity"]] = relationship("ReportGroupEntity", back_populates="report_group_set")
    user_accesses: Mapped[list["UserReportGroupSetAccessEntity"]] = relationship("UserReportGroupSetAccessEntity", back_populates="report_group_set")
