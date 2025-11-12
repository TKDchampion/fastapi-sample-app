from requests import Session
from sqlalchemy import insert
from app.entities.associations_entity import org_business_modules
from datetime import datetime


def add_org_business_module(db: Session, org_id: int, module_ids: list[int]):
    rows = [
        {
            "org_id": org_id,
            "business_modules_id": mid,
            "enabled_at": datetime.utcnow(),
        }
        for mid in module_ids
    ]

    insert_stmt = insert(org_business_modules)
    db.execute(insert_stmt, rows)

    return {
        "org_id": org_id,
        "business_modules_id": module_ids,
        "enabled_at": datetime.utcnow(),
    }
