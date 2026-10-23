from datetime import date

import pytest

from ai_daily.report import (
    ReportNotReady, first_items, item_key, lead_picture, section_rows,
    source_name, validate_report,
)

DAY = date(2026, 10, 22)


def daily():
    return {"date": "2026-10-22", "lead": {"title": "Lead", "leadParagraph": "Full paragraph."},
            "sections": [], "flashes": []}


def test_validate_accepts_payload_and_returns_independent_report():
    original = daily()
    result = validate_report({"report": original}, DAY)
    result["lead"]["title"] = "Changed"
    assert original["lead"]["title"] == "Lead"


@pytest.mark.parametrize("patch", [
    {"date": "2026-10-21"}, {"lead": None},
    {"lead": {"title": "Lead", "leadParagraph": ""}},
    {"sections": "invalid"}, {"sections": [{"items": [None]}]},
])
def test_invalid_or_stale_report_is_not_ready(patch):
    report = daily()
    report.update(patch)
    with pytest.raises(ReportNotReady):
        validate_report(report, DAY)


def test_no_promotion_after_lead_removal():
    lead, later = {"title": "Lead"}, {"title": "Later"}
    report = {"lead": lead, "sections": [{"label": "Industry", "items": [lead, later]}]}
    assert first_items(report) == [lead]
    assert section_rows(report) == [("Industry", [later], False)]


def test_flash_sections_and_flashes_keep_text_but_have_no_artwork():
    first, flash, last = {"title": "First"}, {"title": "Flash"}, {"title": "Last"}
    report = {"sections": [{"label": "Models", "items": [first]},
                           {"label": "快讯", "items": [flash]}, {"items": []}],
              "flashes": [last]}
    assert first_items(report) == [first]
    assert section_rows(report) == [("Models", [first], False), ("快讯", [flash], True), ("快讯", [last], True)]


def test_shared_first_story_generates_once_and_moves_to_lead():
    story = {"title": "Lead", "links": {"aihot": "https://example.test/story"}}
    report = {"lead": {"title": "Lead"}, "sections": [{"items": [story]}, {"items": [story]}]}
    image = object()
    assert first_items(report) == [story]
    assert lead_picture(report, {item_key(story): image}) == (image, story)
    assert section_rows(report) == []


def test_lead_that_is_not_first_does_not_take_another_story_image():
    first, lead = {"title": "First"}, {"title": "Lead"}
    report = {"lead": lead, "sections": [{"items": [first, lead]}]}
    assert lead_picture(report, {"First": object()}) == (None, lead)


def test_source_name_removes_only_trailing_parenthetical_notes():
    assert source_name({"source": {"name": "Lab (Research): Blog（网页） (HTML)"}}) == "Lab (Research): Blog"
    assert source_name({}) == ""
