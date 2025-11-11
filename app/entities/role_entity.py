from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.entities.associations_entity import role_permissions, user_roles


class RoleEntity(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
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

    org: Mapped["OrganizationEntity"] = relationship(
        "OrganizationEntity", back_populates="roles"
    )

    permissions: Mapped[list["PermissionEntity"]] = relationship(
        "PermissionEntity",
        secondary=role_permissions,
        back_populates="roles",
    )

    users: Mapped[list["UserEntity"]] = relationship(
        "UserEntity",
        secondary=user_roles,
        back_populates="roles",
    )
