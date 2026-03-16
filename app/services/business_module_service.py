from typing import Any, AsyncIterator
from sqlalchemy.orm import Session
from app.decorators.db_transaction import db_tx
from app.domain.access_tree.check_user_access import PermissionCheckParams
from app.domain.exception.domain_exception import DomainException
from app.dtos.business_module_dto import BusinessModuleDTO
from app.dtos.insight_dto import InsightAnalysisRequestDTO
from app.dtos.user_dto import UserReadDTO
from app.repositories import business_module_repository
from app.repositories import org_repository
from app.services import insight_service
from app.services.permission_guard_service import verify_user_permission


@db_tx
def get_business_module(db: Session):
    return business_module_repository.get_business_modules(db)


async def get_org_insight_info(
    db: Session, current_user: UserReadDTO, si_id: int, org_id: int
) -> Any:
    """
    Get insight info based on organization's table_location and type.
    """
    verify_user_permission(
        db,
        current_user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="business.insight"),
    )

    org = org_repository.get_org_by_sid_oid(db, si_id, org_id)
    if not org:
        raise DomainException(
            msg=f"Organization {org_id} not found under SI {si_id}",
            type="not_found",
            code=404,
        )
    # Check if org has business module id=2 (insight module)
    has_insight_module = any(m.id == 2 for m in org.business_modules)
    if not has_insight_module:
        raise DomainException(
            msg="Organization does not have access to insight module",
            type="no_access",
            code=403,
        )
    if not org.table_location or not org.type:
        raise DomainException(
            msg="Organization missing table_location or type configuration",
            type="ads_mapping_missing",
            code=400,
        )
    return await insight_service.get_insight_info(
        table_location=org.table_location,
        type=org.type,
    )


async def post_org_insight_analysis_stream(
    db: Session,
    current_user: UserReadDTO,
    si_id: int,
    org_id: int,
    body: InsightAnalysisRequestDTO,
) -> AsyncIterator[bytes]:
    """
    Post insight analysis request and return streaming response.
    Validation runs before returning the stream generator.
    Yields NDJSON bytes from InsightStreamResponseDTO objects.
    """
    verify_user_permission(
        db,
        current_user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="business.insight"),
    )

    org = org_repository.get_org_by_sid_oid(db, si_id, org_id)
    if not org:
        raise DomainException(
            msg=f"Organization {org_id} not found under SI {si_id}",
            type="not_found",
            code=404,
        )
    has_insight_module = any(m.id == 2 for m in org.business_modules)
    if not has_insight_module:
        raise DomainException(
            msg="Organization does not have access to insight module",
            type="no_access",
            code=403,
        )
    if not org.table_location or not org.type:
        raise DomainException(
            msg="Organization missing table_location or type configuration",
            type="ads_mapping_missing",
            code=400,
        )

    async def stream_generator() -> AsyncIterator[bytes]:
        async for dto in insight_service.post_analysis_stream(
            table_location=org.table_location,
            type=org.type,
            ads_str=body.ads_str,
            start_date=body.start_date,
            end_date=body.end_date,
        ):
            yield dto.model_dump_json().encode("utf-8") + b"\n"

    return stream_generator()
