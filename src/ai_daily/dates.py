from datetime import date, datetime
from zoneinfo import ZoneInfo

BEIJING = ZoneInfo("Asia/Shanghai")

def beijing_date(now: datetime) -> date:
    return now.astimezone(BEIJING).date()
