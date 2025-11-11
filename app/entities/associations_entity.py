import datetime
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
    Column,
    ForeignKey,
    UniqueConstraint,
    func,
)
from app.database import Base


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id",
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    PrimaryKeyConstraint("permission_id", "role_id"),
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("scope_type", String, nullable=False),
    Column("scope_id", Integer, nullable=False),
    Column("isActive", Boolean, nullable=True, default=None),
    PrimaryKeyConstraint("user_id", "role_id"),
    UniqueConstraint("user_id", "role_id", "scope_type", "scope_id", "isActive"),
    CheckConstraint("scope_type IN ('super', 'si', 'org')"),
    Index("idx_user_roles_scope_type_scope_id", "scope_type", "scope_id"),
    Index("idx_user_roles_user_id", "user_id"),
)

si_permissions = Table(
    "si_permissions",
    Base.metadata,
    Column("si_id", ForeignKey("si.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id",
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    PrimaryKeyConstraint("si_id", "permission_id"),
)

org_permissions = Table(
    "org_permissions",
    Base.metadata,
    Column(
        "org_id",
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    PrimaryKeyConstraint("org_id", "permission_id"),
)

org_business_modules = Table(
    "org_business_modules",
    Base.metadata,
    Column(
        "org_id", ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "business_modules_id",
        ForeignKey("business_modules.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "enabled_at",
        DateTime,
        default=datetime.datetime.utcnow(),
        server_default=func.now(),
    ),
)
