from datetime import datetime, timezone
from ai_daily.dates import beijing_date

def test_beijing_date_is_next_calendar_day_after_16_utc():
    now = datetime(2026, 10, 20, 16, 30, tzinfo=timezone.utc)
    assert beijing_date(now).isoformat() == "2026-10-21"
