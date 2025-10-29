import enum
from sqlalchemy import Enum, Integer, PrimaryKeyConstraint, Table, Column, ForeignKey
from app.database import Base


class ScopeType(enum.Enum):
    system = "system"
    si = "si"
    org = "org"


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
    Column("scope_type", Enum(ScopeType), nullable=False),
    Column("scope_id", Integer, nullable=False),
    PrimaryKeyConstraint("user_id", "role_id", "scope_type", "scope_id"),
)

user_si = Table(
    "user_si",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("si_id", ForeignKey("si.id", ondelete="CASCADE"), primary_key=True),
    PrimaryKeyConstraint("user_id", "si_id"),
)

user_org = Table(
    "user_org",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "organization_id",
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    PrimaryKeyConstraint("user_id", "organization_id"),
)
