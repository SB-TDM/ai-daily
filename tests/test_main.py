from datetime import datetime, timezone
from ai_daily.__main__ import main

def test_missing_webhook_exits_without_getting_or_posting():
    calls = []
    code = main([], {}, datetime(2026, 10, 21, 1, tzinfo=timezone.utc), lambda url: calls.append(url), lambda html: b"\x89PNG", lambda url, json: calls.append(url))
    assert code == 2
    assert calls == []
