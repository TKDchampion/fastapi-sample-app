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

    si: Mapped["SI"] = relationship("SI", back_populates="organizations")
    roles: Mapped[list["Role"]] = relationship("Role", back_populates="organization")
    users: Mapped[list["User"]] = relationship("User", back_populates="organization")

    org_permission_users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_org_permissions",
        back_populates="org_permissions",
    )
