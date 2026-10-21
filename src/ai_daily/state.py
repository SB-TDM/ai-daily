import json
from datetime import date
from pathlib import Path

def already_sent(path: Path, day: date) -> bool:
    if not path.exists():
        return False
    return day.isoformat() in json.loads(path.read_text(encoding="utf-8"))

def mark_sent(path: Path, day: date) -> None:
    days = []
    if path.exists():
        days = json.loads(path.read_text(encoding="utf-8"))
    if day.isoformat() not in days:
        days.append(day.isoformat())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(days), encoding="utf-8")
