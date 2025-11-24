from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.entities.associations_entity import role_permissions


class PermissionEntity(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False, default="org")
    description: Mapped[str | None] = mapped_column(Text)
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

    roles: Mapped[list["RoleEntity"]] = relationship(
        "RoleEntity",
        secondary=role_permissions,
        back_populates="permissions",
    )
    sis: Mapped[list["SIEntity"]] = relationship(
        "SIEntity",
        secondary="si_permissions",
        back_populates="permissions",
    )
    orgs: Mapped[list["OrganizationEntity"]] = relationship(
        "OrganizationEntity",
        secondary="org_permissions",
        back_populates="permissions",
    )
