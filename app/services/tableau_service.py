import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from jose import jwt
from sqlalchemy.orm import Session

from app.decorators.db_transaction import db_tx
from app.domain.access_tree.check_user_access import PermissionCheckParams
from app.domain.exception.domain_exception import DomainException
from app.dtos.tableau_dto import TableauTokenResponseDTO
from app.dtos.user_dto import UserReadDTO
from app.services.permission_guard_service import verify_user_permission


TABLEAU_ALGORITHM = "HS256"
TABLEAU_EXPIRE_MINUTES = 5
TABLEAU_JWT_SCOPE = "tableau:views:embed"
TABLEAU_JWT_AUDIENCE = "tableau"
TABLEAU_BUSINESS_UNITS = ("BU1", "BU2")


@dataclass(frozen=True)
class TableauConnectedAppConfig:
    client_id: str
    secret_id: str
    secret_value: str
    sub: str


def _get_required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise DomainException(f"{key} is not configured", "tableau_config_missing", 500)
    return value


def _get_optional_int_env(key: str) -> int | None:
    value = os.getenv(key)
    if not value:
        return None

    try:
        return int(value)
    except ValueError:
        raise DomainException(
            f"{key} must be an integer",
            "tableau_config_invalid",
            500,
        )


def _get_connected_app_config(si_id: int) -> TableauConnectedAppConfig:    
    for business_unit in TABLEAU_BUSINESS_UNITS:
        configured_si_id = _get_optional_int_env(f"TABLEAU_{business_unit}_SI_ID")
        if configured_si_id != si_id:
            continue

        return TableauConnectedAppConfig(
            client_id=_get_required_env(
                f"TABLEAU_{business_unit}_CONNECTED_APP_CLIENT_ID"
            ),
            secret_id=_get_required_env(
                f"TABLEAU_{business_unit}_CONNECTED_APP_SECRET_ID"
            ),
            secret_value=_get_required_env(
                f"TABLEAU_{business_unit}_CONNECTED_APP_SECRET_VALUE"
            ),
            sub=_get_required_env(f"TABLEAU_{business_unit}_SUB"),
        )

    raise DomainException("Tableau is not enabled for this SI", "no_access", 403)


def _create_token(
    user: UserReadDTO, config: TableauConnectedAppConfig
) -> TableauTokenResponseDTO:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=TABLEAU_EXPIRE_MINUTES)

    payload = {
        "iss": config.client_id,
        "sub": config.sub,
        "aud": TABLEAU_JWT_AUDIENCE,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
        "scp": [TABLEAU_JWT_SCOPE],
    }
    headers = {
        "kid": config.secret_id,
        "iss": config.client_id,
    }

    token = jwt.encode(
        payload,
        config.secret_value,
        algorithm=TABLEAU_ALGORITHM,
        headers=headers,
    )
    return TableauTokenResponseDTO(token=token, expires_in=TABLEAU_EXPIRE_MINUTES * 60)


@db_tx
def issue_tableau_token(
    db: Session,
    si_id: int,
    org_id: int,
    user: UserReadDTO,
) -> TableauTokenResponseDTO:
    # 先確認這個 SI 有沒有開 Tableau
    config = _get_connected_app_config(si_id)
    # 再確認這個 user 對這個 org 有沒有權限
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="pass"),
    )
    # 最後產出 Tableau token
    return _create_token(user, config)
