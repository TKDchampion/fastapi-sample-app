from __future__ import annotations
from datetime import datetime
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )

    si: Mapped["SIEntity"] = relationship("SIEntity", back_populates="organizations")
    roles: Mapped[list["RoleEntity"]] = relationship(
        "RoleEntity", back_populates="organizations"
    )

    org_permissions: Mapped[list["UserEntity"]] = relationship(
        "UserEntity",
        secondary="org_permissions",
        back_populates="organizations",
    )

    business_modules: Mapped[List["BusinessModuleEntity"]] = relationship(
        secondary="org_business_modules",
        back_populates="organizations",
    )
