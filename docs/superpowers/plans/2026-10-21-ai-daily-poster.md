# AI Daily Poster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one command that reads today's two Upstreams, fills three visual molds, draws one light-anime poster, and sends that single image to a WeCom group.

**Architecture:** A `run_once` function fetches items, asks a model to choose molds, falls back to a fixed fill when the model fills nothing, renders one PNG, and posts it. The Beijing day is marked sent only after WeCom accepts the image. The external clock is not part of this program.

**Tech Stack:** Python 3.11, pytest, httpx, Pillow. Text model: OpenAI-compatible `POST https://www.string.ink/v1/chat/completions`. WeCom group-robot image webhook. The key stays in `OPENAI_API_KEY` and is never written into the repo. There is no character image.

**Spec:** `docs/superpowers/specs/2026-10-21-ai-daily-poster-design.md`

## Global Constraints

- 一条命令。外部时钟在工作日启动它。命令本身不判断周末。这次设计不规定时钟放在哪里。
- Run 只读 agents-radar 的每日 RSS 和 Hugging Face Daily Papers。只要北京时间当天的 Item。不读 X，不爬网页，不使用昨天的 Item。同一篇的英文孪生稿丢掉。
- 一个 Upstream 失败，用另一个。两个都还没有当天内容，这次 Run 结束，但不把今天记成已发。
- 三步：选模具，填标题、一句话、栏目名，再贴上。模具上不印死「论文」或「开源」。栏目名是填进去的字。
- 模具只有三种：大标题板（一条：栏目名、大标题、一句话）、短标题板（一条：栏目名、短标题，不写句子）、双栏板（并排两条，每边只有栏目名和短标题）。
- 一条 Item 只进一个模具。双栏板的两边是两条不同的 Item。当天最多贴 5 个填好的模具，多出来的丢掉。
- 纸上每天都有报头和页脚。报头只标日期，不写期号。页脚只写「内部传阅」，不印网址。纸上不放角色。
- 来源印成短标签，例如「HN · 10-21」，不印网址。正文是中文。产品名保持原文。
- 模型一个模具都没填时，用兜底。最重要的一条用大标题板。其余用短标题板。两条短的可以合成一块双栏板。
- 日报是一张图。群里只发这一张图。拼坏了不发。发不出去，不把今天记成已发。已经发过，就停止。
- 企微 webhook 地址只放在环境变量里，不进仓库。
- 不自建采集平台。不做可点的链接消息。

## File structure

- `src/ai_daily/dates.py` — Beijing calendar date.
- `src/ai_daily/items.py` — `Item` and source-label formatting.
- `src/ai_daily/radar.py` — parse agents-radar RSS for one day.
- `src/ai_daily/hf.py` — parse Hugging Face daily papers for one day.
- `src/ai_daily/fetch.py` — read both Upstreams, tolerate one failure.
- `src/ai_daily/assign.py` — model JSON, validation, fallback.
- `src/ai_daily/poster.py` — text that must appear, and one PNG.
- `src/ai_daily/wecom.py` — image webhook body and POST.
- `src/ai_daily/state.py` — sent-date file.
- `src/ai_daily/run.py` — `run_once` outcomes.
- `src/ai_daily/__main__.py` — `python -m ai_daily`.
- `tests/` — one test module per unit above.

---

### Task 1: Package, Beijing date, Item

**Files:**
- Create: `pyproject.toml`
- Create: `src/ai_daily/__init__.py`
- Create: `src/ai_daily/dates.py`
- Create: `src/ai_daily/items.py`
- Create: `.gitignore`
- Test: `tests/test_dates.py`
- Test: `tests/test_items.py`

**Interfaces:**
- Consumes: nothing
- Produces: `beijing_date(now: datetime) -> date`; `Item(id, title, summary, category, source_label, kind)`; `source_label(origin: str, day: date) -> str`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_dates.py
from datetime import datetime, timezone
from ai_daily.dates import beijing_date

def test_beijing_date_is_next_calendar_day_after_16_utc():
    now = datetime(2026, 10, 20, 16, 30, tzinfo=timezone.utc)
    assert beijing_date(now).isoformat() == "2026-10-21"
```

```python
# tests/test_items.py
from datetime import date
from ai_daily.items import source_label

def test_source_label_has_no_url():
    assert source_label("HN", date(2026, 10, 21)) == "HN · 10-21"
    assert "http" not in source_label("HF", date(2026, 10, 21))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_dates.py tests/test_items.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

`pyproject.toml` requires Python `>=3.11` and dependencies `pytest`, `httpx`, `Pillow`. Package dir is `src`.

`.gitignore` contains `.env`, `.superpowers/`, `data/`, `__pycache__/`, `.pytest_cache/`, `*.png` under `data/`.

```python
# src/ai_daily/dates.py
from datetime import date, datetime
from zoneinfo import ZoneInfo

BEIJING = ZoneInfo("Asia/Shanghai")

def beijing_date(now: datetime) -> date:
    return now.astimezone(BEIJING).date()
```

```python
# src/ai_daily/items.py
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class Item:
    id: str
    title: str
    summary: str
    category: str
    source_label: str
    kind: str

def source_label(origin: str, day: date) -> str:
    return f"{origin} · {day.strftime('%m-%d')}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_dates.py tests/test_items.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

If `git status` fails because this folder is not a repo, run `git init` first. Do not commit `.env` or `data/`.

```powershell
git add pyproject.toml .gitignore src/ai_daily/dates.py src/ai_daily/items.py src/ai_daily/__init__.py tests/test_dates.py tests/test_items.py
git commit -m "feat: add Beijing date and item label"
```

---

### Task 2: agents-radar RSS for one Beijing day

**Files:**
- Create: `src/ai_daily/radar.py`
- Test: `tests/test_radar.py`

**Interfaces:**
- Consumes: `Item`, `source_label`, `date`
- Produces: `parse_radar(xml: str, day: date) -> list[Item]`

- [ ] **Step 1: Write the failing test**

```python
from datetime import date
from ai_daily.radar import parse_radar

XML = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item>
    <title>AI 开源趋势日报 2026-10-21</title>
    <link>https://duanyytop.github.io/agents-radar/#2026-10-21/ai-trending</link>
    <pubDate>Wed, 21 Oct 2026 00:00:00 +0000</pubDate>
    <description>今日亮点 DeepInfer 开源。</description>
  </item>
  <item>
    <title>AI Open Source Trends 2026-10-21</title>
    <link>https://duanyytop.github.io/agents-radar/#2026-10-21/ai-trending-en</link>
    <pubDate>Wed, 21 Oct 2026 00:00:00 +0000</pubDate>
    <description>English twin.</description>
  </item>
  <item>
    <title>AI 开源趋势日报 2026-10-20</title>
    <link>https://duanyytop.github.io/agents-radar/#2026-10-20/ai-trending</link>
    <pubDate>Tue, 20 Oct 2026 00:00:00 +0000</pubDate>
    <description>昨天。</description>
  </item>
  <item>
    <title>趋势报告生成失败 2026-10-21</title>
    <link>https://duanyytop.github.io/agents-radar/#2026-10-21/ai-fail</link>
    <pubDate>Wed, 21 Oct 2026 00:00:00 +0000</pubDate>
    <description>生成失败。</description>
  </item>
</channel></rss>"""

def test_radar_keeps_today_chinese_and_drops_twins_yesterday_and_failures():
    items = parse_radar(XML, date(2026, 10, 21))
    assert [item.title for item in items] == ["AI 开源趋势日报 2026-10-21"]
    assert items[0].source_label == "agents-radar · 10-21"
    assert "http" not in items[0].source_label
    assert items[0].kind == "other"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_radar.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Parse with `xml.etree.ElementTree`. Keep an item only when the link contains `#YYYY-MM-DD/` for `day`, the link does not contain `-en`, and the description does not contain `生成失败`. `id` is the link. `category` is `""` until assign fills it. `summary` is the description text, trimmed. `kind` is `other`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_radar.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/radar.py tests/test_radar.py
git commit -m "feat: parse today's agents-radar items"
```

---

### Task 3: Hugging Face papers and merged fetch

**Files:**
- Create: `src/ai_daily/hf.py`
- Create: `src/ai_daily/fetch.py`
- Test: `tests/test_hf.py`
- Test: `tests/test_fetch.py`

**Interfaces:**
- Consumes: `Item`, `parse_radar`
- Produces: `parse_hf(payload: list[dict], day: date) -> list[Item]`; `UpstreamNotReady`; `fetch_items(day, radar_xml, hf_payload, radar_error, hf_error) -> list[Item]`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_hf.py
from datetime import date
from ai_daily.hf import parse_hf

def test_hf_keeps_papers_published_on_the_beijing_day():
    payload = [
        {"paper": {"id": "2610.26863", "title": "Halcyon", "summary": "从零训练。"}, "publishedAt": "2026-10-21T01:00:00.000Z"},
        {"paper": {"id": "2610.00001", "title": "Old", "summary": "昨天。"}, "publishedAt": "2026-10-20T01:00:00.000Z"},
    ]
    items = parse_hf(payload, date(2026, 10, 21))
    assert [item.id for item in items] == ["2610.26863"]
    assert items[0].kind == "paper"
    assert items[0].source_label == "HF · 10-21"
```

```python
# tests/test_fetch.py
from datetime import date
import pytest
from ai_daily.fetch import UpstreamNotReady, fetch_items

def test_one_upstream_failure_keeps_the_other():
    items = fetch_items(date(2026, 10, 21), radar_xml="<rss><channel></channel></rss>", hf_payload=[{"paper": {"id": "1", "title": "P", "summary": "s"}, "publishedAt": "2026-10-21T00:00:00.000Z"}], radar_error=RuntimeError("down"), hf_error=None)
    assert [item.id for item in items] == ["1"]

def test_both_empty_or_failed_does_not_invent_items():
    with pytest.raises(UpstreamNotReady):
        fetch_items(date(2026, 10, 21), radar_xml="<rss><channel></channel></rss>", hf_payload=[], radar_error=RuntimeError("down"), hf_error=RuntimeError("down"))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_hf.py tests/test_fetch.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

`parse_hf` keeps papers whose `publishedAt` converts to `day` in `Asia/Shanghai`. `kind` is `paper`. `id` is `paper.id`. `title` and `summary` come from the paper. `category` is `""`. `source_label` is `source_label("HF", day)`.

`fetch_items` parses a side only when that side's error is `None`. A parse error or an empty parse contributes `[]`. If the merged list is empty, raise `UpstreamNotReady`. Radar items come first, then HF items. Do not fetch the network in this function.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_hf.py tests/test_fetch.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/hf.py src/ai_daily/fetch.py tests/test_hf.py tests/test_fetch.py
git commit -m "feat: merge today's upstream items"
```

---

### Task 4: Choose molds, validate, fall back

**Files:**
- Create: `src/ai_daily/assign.py`
- Test: `tests/test_assign.py`

**Interfaces:**
- Consumes: `Item`
- Produces: `FilledSide(category: str, title: str, sentence: str, source_label: str)`; `FilledMold(mold: str, sides: tuple[FilledSide, ...])`; `assign(items: list[Item], model_json: str | None) -> list[FilledMold]`

- [ ] **Step 1: Write the failing test**

```python
from ai_daily.assign import assign
from ai_daily.items import Item

def item(i, kind="other"):
    return Item(str(i), f"标题{i}", f"句子{i}", "", f"HN · 10-21", kind)

def test_invalid_model_json_uses_fallback_and_caps_at_five_molds():
    items = [item(i) for i in range(8)]
    molds = assign(items, model_json="not-json")
    assert len(molds) <= 5
    assert molds[0].mold == "lead"
    assert molds[0].sides[0].title == "标题0"
    assert molds[0].sides[0].sentence == "句子0"
    assert all(mold.mold != "lead" for mold in molds[1:])
    assert all(side.sentence == "" for mold in molds if mold.mold != "lead" for side in mold.sides)
    assert all(len(mold.sides) == 2 for mold in molds if mold.mold == "pair")

def test_unknown_mold_name_is_rejected_and_fallback_does_not_repeat():
    items = [item(1), item(2, "paper")]
    raw = '{"molds":[{"mold":"论文","sides":[{"item_id":"1","category":"论文","title":"标题1","sentence":"句子1"}]}]}'
    molds = assign(items, model_json=raw)
    assert molds[0].mold == "lead"
    assert molds[0].sides[0].title == "标题1"
    assert "http" not in molds[0].sides[0].source_label
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_assign.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class FilledSide:
    category: str
    title: str
    sentence: str
    source_label: str

@dataclass(frozen=True)
class FilledMold:
    mold: str  # lead, short, pair
    sides: tuple[FilledSide, ...]
```

Model JSON shape, and the only accepted mold names:

```json
{"molds":[{"mold":"lead","sides":[{"item_id":"0","category":"开源","title":"标题0","sentence":"句子0"}]}]}
```

Accept the JSON only when every mold name is `lead`, `short`, or `pair`, every `item_id` exists, a `pair` has two different ids, and no id is used twice. Copy `source_label` from the Item. Ignore any URL field. Force `sentence` to `""` on `short` and `pair`. Keep at most 5 molds. If the JSON is missing, invalid, or yields zero molds, fall back. Fallback treats the first merged item as the most important: one `lead` with `title=item.title` and `sentence=item.summary`. Remaining items become `pair` molds two at a time. A leftover item is one `short`. Stop at 5 molds. Fallback category comes from `kind`: `paper` is `论文`, `repo` is `开源`, `product` is `产品`, otherwise `要闻`. That word is filled text, not a mold name.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_assign.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/assign.py tests/test_assign.py
git commit -m "feat: fill molds or fall back"
```

---

### Task 5: Draw one poster

**Files:**
- Create: `src/ai_daily/poster.py`
- Test: `tests/test_poster.py`

**Interfaces:**
- Consumes: `FilledMold`, `FilledSide`, `date`
- Produces: `poster_lines(day: date, molds: list[FilledMold]) -> list[str]`; `render_png(day: date, molds: list[FilledMold]) -> bytes`

- [ ] **Step 1: Write the failing test**

```python
from datetime import date
from ai_daily.assign import FilledMold, FilledSide
from ai_daily.poster import poster_lines, render_png

def test_poster_has_date_footer_and_filled_words_but_no_url_or_issue_number():
    molds = [FilledMold("lead", (FilledSide("开源", "把推理框架交出去", "用来降低开销。", "HN · 10-21"),))]
    lines = poster_lines(date(2026, 10, 21), molds)
    text = "\n".join(lines)
    assert "2026年10月21日" in text
    assert "内部传阅" in text
    assert "把推理框架交出去" in text
    assert "开源" in text
    assert "http" not in text
    assert "第" not in text
    png = render_png(date(2026, 10, 21), molds)
    assert png.startswith(b"\x89PNG")
    assert len(png) < 2_000_000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_poster.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

`poster_lines` always starts with `AI 日报` and the date as `2026年10月21日`, then one block per mold, then exactly `内部传阅`. A lead block includes category, title, sentence, and source label. A short block and each pair side include category, title, and source label, and omit the sentence. Do not write a URL, `第`, `样式稿`, or `全文见当日 Upstream`.

`render_png` draws a 720×1280 RGB image. Paper is `(251, 246, 248)`. Ink is `(43, 33, 64)`. Accent is `(226, 62, 120)`. Do not draw or paste a character. Do not call an image API. Draw mold blocks under the masthead. Category text sits on an accent rounded sticker. A `pair` is two columns. Use `C:\Windows\Fonts\msyh.ttc` when that file exists, otherwise Pillow's default font. Save PNG bytes.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_poster.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/poster.py tests/test_poster.py
git commit -m "feat: render one poster image"
```

---

### Task 6: WeCom image post and sent-date file

**Files:**
- Create: `src/ai_daily/wecom.py`
- Create: `src/ai_daily/state.py`
- Test: `tests/test_wecom.py`
- Test: `tests/test_state.py`

**Interfaces:**
- Consumes: PNG bytes, `date`, `Path`
- Produces: `image_body(png: bytes) -> dict`; `post_image(png: bytes, webhook_url: str, post) -> None`; `already_sent(path: Path, day: date) -> bool`; `mark_sent(path: Path, day: date) -> None`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_wecom.py
import hashlib, base64
from ai_daily.wecom import image_body, post_image

def test_image_body_is_base64_and_md5_and_not_a_link_message():
    png = b"\x89PNG-fake"
    body = image_body(png)
    assert body["msgtype"] == "image"
    assert body["image"]["base64"] == base64.b64encode(png).decode()
    assert body["image"]["md5"] == hashlib.md5(png).hexdigest()
    assert "markdown" not in body

def test_post_image_refuses_a_non_ok_wecom_response():
    calls = []
    def post(url, json):
        calls.append((url, json))
        return {"errcode": 93000, "errmsg": "invalid"}
    try:
        post_image(b"\x89PNG", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=secret", post)
        assert False
    except RuntimeError:
        assert calls[0][0].endswith("key=secret")
```

```python
# tests/test_state.py
from datetime import date
from pathlib import Path
from ai_daily.state import already_sent, mark_sent

def test_day_is_open_until_mark_sent(tmp_path: Path):
    path = tmp_path / "sent.json"
    day = date(2026, 10, 21)
    assert already_sent(path, day) is False
    mark_sent(path, day)
    assert already_sent(path, day) is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_wecom.py tests/test_state.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

`post_image` calls `post(webhook_url, image_body(png))`. Raise `RuntimeError` unless the dict has `errcode == 0`. `state` stores a JSON list of `YYYY-MM-DD` strings. Missing file means not sent.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_wecom.py tests/test_state.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/wecom.py src/ai_daily/state.py tests/test_wecom.py tests/test_state.py
git commit -m "feat: send one image and record the day"
```

---

### Task 7: run_once

**Files:**
- Create: `src/ai_daily/run.py`
- Test: `tests/test_run.py`

**Interfaces:**
- Consumes: `already_sent`, `mark_sent`, `fetch_items`, `assign`, `render_png`, `post_image`, `UpstreamNotReady`
- Produces: `run_once(day, state_path, radar_xml, hf_payload, radar_error, hf_error, model_json, post) -> str` returning `already-sent`, `not-ready`, `sent`, or `delivery-failed`

- [ ] **Step 1: Write the failing test**

```python
from datetime import date
from pathlib import Path
from ai_daily.run import run_once
from ai_daily.state import already_sent

DAY = date(2026, 10, 21)
HF = [{"paper": {"id": "1", "title": "Halcyon", "summary": "从零训练。"}, "publishedAt": "2026-10-21T00:00:00.000Z"}]

def test_already_sent_does_not_post(tmp_path: Path):
    from ai_daily.state import mark_sent
    mark_sent(tmp_path / "sent.json", DAY)
    calls = []
    result = run_once(DAY, tmp_path / "sent.json", "", [], None, None, None, lambda url, json: calls.append(url))
    assert result == "already-sent"
    assert calls == []

def test_not_ready_does_not_mark_sent(tmp_path: Path):
    path = tmp_path / "sent.json"
    result = run_once(DAY, path, "<rss><channel></channel></rss>", [], RuntimeError("x"), RuntimeError("y"), None, lambda url, json: None)
    assert result == "not-ready"
    assert already_sent(path, DAY) is False

def test_webhook_failure_does_not_mark_sent(tmp_path: Path):
    path = tmp_path / "sent.json"
    def post(url, json):
        return {"errcode": 1, "errmsg": "no"}
    result = run_once(DAY, path, "<rss><channel></channel></rss>", HF, None, None, None, post)
    assert result == "delivery-failed"
    assert already_sent(path, DAY) is False

def test_success_marks_sent_and_posts_one_image(tmp_path: Path):
    path = tmp_path / "sent.json"
    calls = []
    def post(url, json):
        calls.append(json)
        return {"errcode": 0, "errmsg": "ok"}
    result = run_once(DAY, path, "<rss><channel></channel></rss>", HF, None, None, None, post)
    assert result == "sent"
    assert calls[0]["msgtype"] == "image"
    assert already_sent(path, DAY) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_run.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Order: if `already_sent`, return `already-sent`. Call `fetch_items`. On `UpstreamNotReady`, return `not-ready`. `assign` with `model_json`. `render_png`. On any exception from render, return `delivery-failed` and do not call `post`. `post_image`. On exception, return `delivery-failed`. Only then `mark_sent` and return `sent`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_run.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/run.py tests/test_run.py
git commit -m "feat: close the day only after a sent poster"
```

---

### Task 8: Command entry

**Files:**
- Create: `src/ai_daily/__main__.py`
- Create: `src/ai_daily/model.py`
- Test: `tests/test_main.py`

**Interfaces:**
- Consumes: `run_once`, `beijing_date`, httpx
- Produces: `main(argv: list[str], environ: dict, now, get, post) -> int`

- [ ] **Step 1: Write the failing test**

```python
from datetime import datetime, timezone
from ai_daily.__main__ import main

def test_missing_webhook_env_exits_without_posting():
    code = main([], {}, datetime(2026, 10, 21, 1, tzinfo=timezone.utc), lambda url: "", lambda url, json: {"errcode": 0})
    assert code == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_main.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

`main` reads `WECOM_WEBHOOK_URL` from `environ`. If missing, return `2`. Do not read a webhook from argv. GET these constants: `https://duanyytop.github.io/agents-radar/feed.xml` and `https://huggingface.co/api/daily_papers`. A GET exception becomes that side's error and an empty payload. If `OPENAI_API_KEY` is absent or the model call fails, pass `model_json=None`. State path is `environ.get("AI_DAILY_STATE_PATH", "data/sent.json")`. Print the `run_once` result. Return `0` for `sent` and `already-sent`. Return `1` for `not-ready` and `delivery-failed`.

`model.py` POSTs `{base}/chat/completions` with `base = environ.get("OPENAI_BASE_URL", "https://www.string.ink/v1")`. The user message is exactly:

```text
只返回 JSON。模具名只能是 lead、short、pair。栏目名写在 category，不要把栏目名当成模具名。一条 item_id 只用一次。pair 必须是两条不同的 item_id。最多 5 个模具。句子用中文。产品名保持原文。不要输出网址。
```

The request also includes the item ids, titles, summaries, and kinds. Parse `choices[0].message.content` as the `model_json` string. Do not log the API key or the webhook URL.

- [ ] **Step 4: Run the full test suite**

Run: `python -m pytest -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/__main__.py src/ai_daily/model.py tests/test_main.py
git commit -m "feat: add the daily poster command"
```
