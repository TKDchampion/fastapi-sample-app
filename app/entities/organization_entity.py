from __future__ import annotations
from datetime import datetime, timezone
from typing import List
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class OrganizationEntity(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    si_id: Mapped[int] = mapped_column(
        ForeignKey("si.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    logo: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text)
    disabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    table_location: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[str | None] = mapped_column(String, nullable=True)
    contract_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    contract_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
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

    si: Mapped["SIEntity"] = relationship("SIEntity", back_populates="orgs")
    roles: Mapped[list["RoleEntity"]] = relationship("RoleEntity", back_populates="org")

    permissions: Mapped[list["PermissionEntity"]] = relationship(
        "PermissionEntity",
        secondary="org_permissions",
        back_populates="orgs",
    )

    business_modules: Mapped[List["BusinessModuleEntity"]] = relationship(
        secondary="org_business_modules",
        back_populates="organizations",
    )

    report_group_sets: Mapped[list["ReportGroupSetEntity"]] = relationship(
        "ReportGroupSetEntity", back_populates="org"
    )

    alert_schedules: Mapped[list["AlertScheduleEntity"]] = relationship(
        "AlertScheduleEntity", back_populates="organization"
    )
