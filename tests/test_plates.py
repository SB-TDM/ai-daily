from ai_daily.plates import assign_plates


def test_lead_title_is_not_repeated_in_later_plates():
    plates = assign_plates(
        {
            "lead": {"title": "头版", "leadParagraph": "一句。"},
            "sections": [
                {
                    "label": "行业",
                    "items": [
                        {"title": "头版", "summary": "不该再出现。"},
                        {"title": "导读一", "summary": "一。"},
                        {"title": "导读二", "summary": "二。"},
                        {"title": "导读三", "summary": "三。"},
                    ],
                }
            ],
            "flashes": [],
        },
        on="2026-10-22",
    )

    later = [item["title"] for item in plates["导读"]]
    assert later == ["导读一", "导读二", "导读三"]
    assert "底栏" not in plates


def test_missing_lead_does_not_assign_plates():
    assert assign_plates({"sections": [], "flashes": []}) is None


def test_items_after_the_lead_fill_index_then_bottom():
    plates = assign_plates(
        {
            "lead": {
                "title": "头版标题",
                "leadParagraph": "导语第一句。导语第二句。",
                "source": {"name": "来源甲"},
            },
            "sections": [
                {
                    "label": "论文",
                    "items": [
                        {"title": "导读一", "summary": "不应出现在导读。"},
                        {"title": "导读二", "summary": "二。"},
                        {"title": "导读三", "summary": "三。"},
                        {"title": "底栏一", "summary": "底一第一句。底一第二句。"},
                    ],
                }
            ],
            "flashes": [{"title": "快讯一", "summary": "快讯这句。后面不算。"}],
        },
        on="2026-10-22",
    )

    assert plates["报头"] == {
        "name": "AI 日报",
        "date": "2026-10-22",
        "weekday": "星期四",
        "mark": "内部阅读",
    }
    assert plates["导读"] == [
        {"label": "论文", "title": "导读一"},
        {"label": "论文", "title": "导读二"},
        {"label": "论文", "title": "导读三"},
    ]
    assert plates["头版"] == {
        "title": "头版标题",
        "paragraph": "导语第一句。导语第二句。",
        "source": "来源甲",
    }
    assert plates["主图位"] == {"title": "头版标题"}
    assert plates["底栏"] == [
        {"label": "论文", "title": "底栏一", "summary": "底一第一句。"},
        {"label": "快讯", "title": "快讯一", "summary": "快讯这句。"},
    ]
    assert plates["页脚"] == "内部阅读"
    assert "不应出现在导读" not in str(plates["导读"])


def test_long_lead_and_summary_are_cut_and_marked():
    plates = assign_plates(
        {
            "lead": {
                "title": "标题",
                "leadParagraph": "甲" * 81,
                "source": {"name": "甲"},
            },
            "sections": [
                {
                    "label": "论文",
                    "items": [
                        {"title": "一", "summary": "短。"},
                        {"title": "二", "summary": "短。"},
                        {"title": "三", "summary": "短。"},
                        {"title": "四", "summary": "乙" * 41},
                    ],
                }
            ],
            "flashes": [],
        },
        on="2026-10-22",
    )

    assert plates["头版"]["paragraph"] == ("甲" * 80) + "…"
    assert plates["底栏"][0]["summary"] == ("乙" * 40) + "…"


def test_empty_index_and_bottom_are_left_out():
    plates = assign_plates(
        {
            "lead": {"title": "只有头版", "leadParagraph": "一句。"},
            "sections": [],
            "flashes": [],
        },
        on="2026-10-22",
    )

    assert "导读" not in plates
    assert "底栏" not in plates
    assert "source" not in plates["头版"]
    assert plates["主图位"] == {"title": "只有头版"}
    assert plates["页脚"] == "内部阅读"
