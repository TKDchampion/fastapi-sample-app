from sqlalchemy.orm import Session
from sqlalchemy import delete, insert, select, update
from app.entities.associations_entity import org_business_modules
from datetime import datetime

from app.entities.business_module_entity import BusinessModuleEntity


def add_org_business_module(db: Session, org_id: int, module_ids: list[int]):
    if module_ids:
        valid_ids = db.scalars(
            select(BusinessModuleEntity.id).where(
                BusinessModuleEntity.id.in_(module_ids)
            )
        ).all()

        missing = set(module_ids) - set(valid_ids)
        if missing:
            raise ValueError(f"Invalid business_modules_id")

    existing_ids = db.scalars(
        select(org_business_modules.c.business_modules_id).where(
            org_business_modules.c.org_id == org_id
        )
    ).all()

    if set(existing_ids) != set(module_ids):
        db.execute(
            delete(org_business_modules).where(org_business_modules.c.org_id == org_id)
        )

        now = datetime.utcnow()
        rows = [
            {"org_id": org_id, "business_modules_id": mid, "enabled_at": now}
            for mid in module_ids
        ]
        if rows:
            result = db.execute(
                insert(org_business_modules).returning(
                    org_business_modules.c.business_modules_id
                ),
                rows,
            )
            inserted_ids = result.scalars().all()
        else:
            inserted_ids = []
    else:
        inserted_ids = existing_ids

    return inserted_ids
