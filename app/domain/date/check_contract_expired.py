from datetime import datetime


def is_contract_isExpired(start: datetime | None, end: datetime | None) -> bool:
    now = datetime.utcnow()
    return not (start <= now <= end)
