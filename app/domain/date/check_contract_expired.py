from datetime import datetime, timezone


def is_contract_isExpired(start: datetime | None, end: datetime | None) -> bool:
    now = datetime.now(timezone.utc)
    return start <= now <= end
