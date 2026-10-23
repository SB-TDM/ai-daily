from datetime import date
from ai_daily.items import source_label

def test_source_label_has_no_url():
    assert source_label("HN", date(2026, 10, 21)) == "HN · 10-21"
    assert "http" not in source_label("HF", date(2026, 10, 21))
