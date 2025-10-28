from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SIEntity(Base):
    __tablename__ = "si"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    organizations: Mapped[list["Organization"]] = relationship(
        "Organization", back_populates="si"
    )
    users: Mapped[list["User"]] = relationship("User", back_populates="si")

    si_permission_users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_si_permissions",
        back_populates="si_permissions",
    )
