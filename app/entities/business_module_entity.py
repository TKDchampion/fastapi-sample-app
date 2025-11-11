from __future__ import annotations
from datetime import datetime
from typing import List
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class BusinessModuleEntity(Base):
    __tablename__ = "business_modules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )

    organizations: Mapped[List["OrganizationEntity"]] = relationship(
        secondary="org_business_modules",
        back_populates="business_modules",
    )
