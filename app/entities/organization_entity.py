from __future__ import annotations
from datetime import datetime
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
        "RoleEntity", back_populates="organization"
    )
    users: Mapped[list["UserEntity"]] = relationship(
        "UserEntity", back_populates="organization"
    )

    org_permission_users: Mapped[list["UserEntity"]] = relationship(
        "UserEntity",
        secondary="user_org_permissions",
        back_populates="org_permissions",
    )
