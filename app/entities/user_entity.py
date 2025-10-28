from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.entities.associations_entity import (
    user_roles,
    user_si_permissions,
    user_org_permissions,
)

# from app.entities.role_entity import RoleEntity
# from app.entities.si_entity import SIEntity
# from app.entities.organization_entity import OrganizationEntity


class UserEntity(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    picture: Mapped[str | None] = mapped_column(String)

    si_id: Mapped[int | None] = mapped_column(ForeignKey("si.id", ondelete="SET NULL"))
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )

    si: Mapped["SIEntity"] = relationship("SIEntity", back_populates="users")
    organization: Mapped["OrganizationEntity"] = relationship(
        "OrganizationEntity", back_populates="users"
    )

    roles: Mapped[list["RoleEntity"]] = relationship(
        "RoleEntity",
        secondary=user_roles,
        back_populates="users",
    )

    si_permissions: Mapped[list["SIEntity"]] = relationship(
        "SIEntity",
        secondary=user_si_permissions,
        back_populates="si_permission_users",
    )

    org_permissions: Mapped[list["OrganizationEntity"]] = relationship(
        "OrganizationEntity",
        secondary=user_org_permissions,
        back_populates="org_permission_users",
    )
