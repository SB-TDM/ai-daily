"""Daily report boundaries and original-first-story illustration selection."""
from copy import deepcopy
import re

_TAIL = re.compile(r"(?:（[^）]*）|\([^)]*\))\s*$")


class ReportNotReady(ValueError):
    pass


def validate_report(payload, day):
    report = payload.get("report", payload) if isinstance(payload, dict) else None
    if not isinstance(report, dict) or report.get("date") != day.isoformat():
        raise ReportNotReady("No current-day report")
    lead = report.get("lead")
    if not isinstance(lead, dict) or any(
        not isinstance(lead.get(key), str) or not lead[key].strip()
        for key in ("title", "leadParagraph")
    ):
        raise ReportNotReady("Missing lead")
    sections, flashes = report.get("sections") or [], report.get("flashes") or []
    if not isinstance(sections, list) or not isinstance(flashes, list):
        raise ReportNotReady("Invalid story collections")
    stories = list(flashes)
    for section in sections:
        if not isinstance(section, dict) or not isinstance(section.get("items") or [], list):
            raise ReportNotReady("Invalid section")
        if not isinstance(section.get("label") or "", str):
            raise ReportNotReady("Invalid section label")
        stories.extend(section.get("items") or [])
    for story in stories:
        if not isinstance(story, dict) or not isinstance(story.get("title"), str) or not story["title"].strip():
            raise ReportNotReady("Invalid story")
        if not isinstance(story.get("summary") or "", str):
            raise ReportNotReady("Invalid summary")
        for key in ("source", "links"):
            if not isinstance(story.get(key) or {}, dict):
                raise ReportNotReady("Invalid story metadata")
        if not isinstance((story.get("source") or {}).get("name") or "", str):
            raise ReportNotReady("Invalid source name")
        if not isinstance((story.get("links") or {}).get("aihot") or "", str):
            raise ReportNotReady("Invalid story identity")
    return deepcopy(report)


def item_key(item):
    return (item.get("links") or {}).get("aihot") or item.get("title") or ""


def clean_source(name):
    cleaned = (name or "").strip()
    while True:
        next_name = _TAIL.sub("", cleaned).strip()
        if next_name == cleaned:
            return cleaned
        cleaned = next_name


def source_name(item):
    return clean_source((item.get("source") or {}).get("name") or "")


def first_items(report):
    selected, seen = [], set()
    for section in report.get("sections") or []:
        if (section.get("label") or "").strip() == "快讯":
            continue
        items = section.get("items") or []
        if not items:
            continue
        story = items[0]
        key = item_key(story)
        if key and key not in seen:
            seen.add(key)
            selected.append(story)
    return selected


def section_rows(report):
    title = (report.get("lead") or {}).get("title") or ""
    rows = []
    for section in report.get("sections") or []:
        label = section.get("label") or ""
        items = [item for item in section.get("items") or [] if item.get("title") != title]
        if items:
            rows.append((label, items, label.strip() == "快讯"))
    flashes = [item for item in report.get("flashes") or [] if item.get("title") != title]
    if flashes:
        rows.append(("快讯", flashes, True))
    return rows


def lead_picture(report, pictures):
    title = (report.get("lead") or {}).get("title") or ""
    source_story = None
    for section in report.get("sections") or []:
        items = section.get("items") or []
        for item in items:
            if item.get("title") == title:
                source_story = item
                break
        if items and items[0].get("title") == title and (section.get("label") or "").strip() != "快讯":
            return pictures.get(item_key(items[0])), items[0]
    return None, source_story
