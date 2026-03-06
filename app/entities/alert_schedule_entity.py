from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AlertScheduleEntity(Base):
    __tablename__ = "alert_schedule"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    schedule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, nullable=False)
    send_schedule: Mapped[str] = mapped_column(String(255), nullable=False)
    interval: Mapped[str | None] = mapped_column(String(255))
    ads_str: Mapped[str] = mapped_column(String(255), nullable=False)
    send_email: Mapped[str] = mapped_column(String, nullable=False)

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

    organization: Mapped["OrganizationEntity"] = relationship(
        "OrganizationEntity", back_populates="alert_schedules"
    )
    user: Mapped["UserEntity"] = relationship(
        "UserEntity", back_populates="alert_schedules"
    )
