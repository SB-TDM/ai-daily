from datetime import datetime, timedelta, timezone

BEIJING = timezone(timedelta(hours=8))


def beijing_date(now=None):
    now = now if now is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("An aware datetime is required")
    return now.astimezone(BEIJING).date()
