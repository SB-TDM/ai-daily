import re
from dataclasses import dataclass
from datetime import date

_TAIL = re.compile(r"(?:（[^）]*）|\([^)]*\))\s*$")

def clean_source(name: str) -> str:
    cleaned = name.strip()
    while True:
        nxt = _TAIL.sub("", cleaned).strip()
        if nxt == cleaned:
            return cleaned
        cleaned = nxt


@dataclass(frozen=True)
class Story:
    title: str
    summary: str
    source_name: str


@dataclass(frozen=True)
class Section:
    label: str
    stories: tuple[Story, ...]


@dataclass(frozen=True)
class Daily:
    day: date
    lead_title: str
    lead_paragraph: str
    sections: tuple[Section, ...]


class DailyNotReady(Exception):
    pass


def parse_daily(payload: dict, day: date) -> Daily:
    report = payload.get("report")
    lead = report.get("lead") if isinstance(report, dict) else None
    title = (lead or {}).get("title") or ""
    paragraph = (lead or {}).get("leadParagraph") or ""
    if not isinstance(report, dict) or report.get("date") != day.isoformat() or not title or not paragraph:
        raise DailyNotReady()
    sections = []
    for raw in report.get("sections") or []:
        label = raw.get("label") or ""
        if label == "快讯":
            continue
        stories = tuple(
            Story(item.get("title") or "", item.get("summary") or "", clean_source((item.get("source") or {}).get("name") or ""))
            for item in raw.get("items") or []
        )
        if stories:
            sections.append(Section(label, stories))
    return Daily(day, title, paragraph, tuple(sections))
