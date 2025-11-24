from datetime import datetime, timezone


def is_contract_isExpired(start: datetime | None, end: datetime | None) -> bool:
    now = lambda: datetime.now(timezone.utc)()
    return not (start <= now <= end)
