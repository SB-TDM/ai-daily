from datetime import date
from pathlib import Path
from ai_daily.state import already_sent, mark_sent

def test_day_is_open_until_mark_sent(tmp_path: Path):
    path = tmp_path / "sent.json"
    day = date(2026, 10, 21)
    assert already_sent(path, day) is False
    mark_sent(path, day)
    assert already_sent(path, day) is True
