from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SIEntity(Base):
    __tablename__ = "si"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
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

    organizations: Mapped[list["OrganizationEntity"]] = relationship(
        "OrganizationEntity", back_populates="si"
    )

    si_users: Mapped[list["UserEntity"]] = relationship(
        "UserEntity",
        secondary="user_si",
        back_populates="si",
    )
