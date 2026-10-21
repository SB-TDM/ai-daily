# AIHOT Daily Screenshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one command that reads today's aihot.news daily, screenshots our own HTML page, and sends that single image to a WeCom group.

**Architecture:** `run_once` fetches nothing by itself. It parses an aihot daily payload, renders HTML, asks a shooter for one PNG, and posts that image. The Beijing day is marked sent only after WeCom accepts it. The browser and the webhook client are injected at the command edge so tests do not open a network.

**Tech Stack:** Python 3.11, pytest, httpx, Playwright Chromium. WeCom group-robot image webhook. No model API.

**Spec:** `docs/superpowers/specs/2026-10-21-ai-daily-poster-design.md`

Do not execute `docs/superpowers/plans/2026-10-21-ai-daily-poster.md`. That plan is obsolete.

## Global Constraints

- 一条命令。外部时钟在工作日启动它。命令本身不判断周末。这次设计不规定时钟放在哪里。
- Run 只读 `https://aihot.news/api/v1/dailies/` 加上北京时间当天的日期。不读 agents-radar，不读 Hugging Face，不读 X，不截 aihot 的网页，也不使用昨天的日报。
- 当天日报还没有，这次 Run 结束，但不把今天记成已发。
- 不调用模型。文案用 aihot 写好的标题、导语和摘要。
- HTML 只是印版，不发给群。截坏了不发。图超过 2MB 也不发。两种情况都不把今天记成已发。
- 报头写「AI 日报」和日期，例如「2026年10月21日」。不写期号。纸上不放角色。
- 头条用接口里的标题和导语。下面按接口里的栏目往下排。每条印标题、摘要、来源名。来源名去掉括号尾巴。不印网址。
- `flashes` 不画。栏目名是「快讯」的也不画。
- 页脚只写「内部传阅」。
- 群里只发这一张图。发不出去，也不把今天记成已发。已经发过，就停止。
- 企微 webhook 地址只放在环境变量里，不进仓库。

## File structure

- `src/ai_daily/dates.py` — Beijing calendar date.
- `src/ai_daily/aihot.py` — parse one daily payload into lead and sections.
- `src/ai_daily/html.py` — the print page.
- `src/ai_daily/shot.py` — accept one PNG, and the Playwright shooter.
- `src/ai_daily/wecom.py` — image webhook body and POST.
- `src/ai_daily/state.py` — sent-date file.
- `src/ai_daily/run.py` — `run_once` outcomes.
- `src/ai_daily/__main__.py` — `python -m ai_daily`.
- `tests/` — one test module per unit above.

---

### Task 1: Package, Beijing date, source-name cleanup

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/ai_daily/__init__.py`
- Create: `src/ai_daily/dates.py`
- Create: `src/ai_daily/aihot.py`
- Test: `tests/test_dates.py`
- Test: `tests/test_source.py`

**Interfaces:**
- Consumes: nothing
- Produces: `beijing_date(now: datetime) -> date`; `clean_source(name: str) -> str`

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
# tests/test_source.py
from ai_daily.aihot import clean_source

def test_clean_source_drops_a_trailing_parenthetical():
    assert clean_source("Inception Labs：Blog（网页）") == "Inception Labs：Blog"
    assert clean_source("公众号：DeepSeek（深度求索）") == "公众号：DeepSeek"
    assert clean_source("X：ChatGPT (@ChatGPT)") == "X：ChatGPT"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_dates.py tests/test_source.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

`pyproject.toml` requires Python `>=3.11`. Dependencies are `pytest`, `httpx`, and `playwright`. Package dir is `src`.

`.gitignore` contains `.env`, `.superpowers/`, `data/`, `__pycache__/`, `.pytest_cache/`, `assets/`.

```python
# src/ai_daily/dates.py
from datetime import date, datetime
from zoneinfo import ZoneInfo

BEIJING = ZoneInfo("Asia/Shanghai")

def beijing_date(now: datetime) -> date:
    return now.astimezone(BEIJING).date()
```

```python
# src/ai_daily/aihot.py
import re

_TAIL = re.compile(r"(?:（[^）]*）|\([^)]*\))\s*$")

def clean_source(name: str) -> str:
    cleaned = name.strip()
    while True:
        nxt = _TAIL.sub("", cleaned).strip()
        if nxt == cleaned:
            return cleaned
        cleaned = nxt
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_dates.py tests/test_source.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

If `git status` fails because this folder is not a repo, run `git init` first. Do not commit `.env` or `data/`.

```powershell
git add pyproject.toml .gitignore src/ai_daily/__init__.py src/ai_daily/dates.py src/ai_daily/aihot.py tests/test_dates.py tests/test_source.py
git commit -m "feat: add Beijing date and source cleanup"
```

---

### Task 2: Parse today's aihot daily

**Files:**
- Modify: `src/ai_daily/aihot.py`
- Test: `tests/test_aihot.py`

**Interfaces:**
- Consumes: `clean_source`, `date`
- Produces: `DailyNotReady`; `Story(title: str, summary: str, source_name: str)`; `Section(label: str, stories: tuple[Story, ...])`; `Daily(day: date, lead_title: str, lead_paragraph: str, sections: tuple[Section, ...])`; `parse_daily(payload: dict, day: date) -> Daily`

- [ ] **Step 1: Write the failing test**

```python
from datetime import date
import pytest
from ai_daily.aihot import DailyNotReady, parse_daily

PAYLOAD = {
    "report": {
        "date": "2026-10-21",
        "lead": {"title": "DeepSeek 开源 DeepInfer", "leadParagraph": "同步开源 deepseek-recipe。"},
        "sections": [
            {"label": "模型发布/更新", "items": [{"title": "Mercury 3", "summary": "速度达 1068 tokens/秒。", "source": {"name": "Inception Labs：Blog（网页）"}}]},
            {"label": "快讯", "items": [{"title": "不该出现", "summary": "快讯。", "source": {"name": "X"}}]},
        ],
        "flashes": [{"title": "也不该出现", "source": {"name": "X"}}],
    }
}

def test_parse_keeps_lead_and_sections_but_drops_flashes_and_urls():
    daily = parse_daily(PAYLOAD, date(2026, 10, 21))
    assert daily.lead_title == "DeepSeek 开源 DeepInfer"
    assert daily.lead_paragraph == "同步开源 deepseek-recipe。"
    assert [section.label for section in daily.sections] == ["模型发布/更新"]
    assert daily.sections[0].stories[0].source_name == "Inception Labs：Blog"
    assert "http" not in daily.sections[0].stories[0].source_name

def test_yesterday_or_missing_report_is_not_ready():
    with pytest.raises(DailyNotReady):
        parse_daily({"report": {"date": "2026-10-20", "lead": {"title": "旧", "leadParagraph": "旧"}}}, date(2026, 10, 21))
    with pytest.raises(DailyNotReady):
        parse_daily({}, date(2026, 10, 21))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_aihot.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from datetime import date

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_aihot.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/aihot.py tests/test_aihot.py
git commit -m "feat: parse today's aihot daily"
```

---

### Task 3: Render the print page

**Files:**
- Create: `src/ai_daily/html.py`
- Test: `tests/test_html.py`

**Interfaces:**
- Consumes: `Daily`, `Section`, `Story`
- Produces: `render_html(daily: Daily) -> str`

- [ ] **Step 1: Write the failing test**

```python
from datetime import date
from ai_daily.aihot import Daily, Section, Story
from ai_daily.html import render_html

def test_page_has_masthead_lead_section_and_footer_without_url_or_issue():
    daily = Daily(
        date(2026, 10, 21),
        "DeepSeek <开源>",
        "同步开源。",
        (Section("模型发布/更新", (Story("Mercury 3", "速度达 1068 tokens/秒。", "Inception Labs：Blog"),)),),
    )
    html = render_html(daily)
    assert "AI 日报" in html
    assert "2026年10月21日" in html
    assert "DeepSeek &lt;开源&gt;" in html
    assert "同步开源。" in html
    assert "模型发布/更新" in html
    assert "Mercury 3" in html
    assert "内部传阅" in html
    assert "http" not in html
    assert "第" not in html
    assert "快讯" not in html
    assert "角色" not in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_html.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

```python
from html import escape
from ai_daily.aihot import Daily

def render_html(daily: Daily) -> str:
    day = daily.day
    blocks = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>",
        "<body style='margin:0;background:#fbf6f8;color:#2b2140;font-family:Microsoft YaHei,sans-serif'>",
        "<article style='width:720px;padding:24px'>",
        f"<h1>AI 日报</h1><p>{day.year}年{day.month}月{day.day}日</p>",
        f"<h2>{escape(daily.lead_title)}</h2><p>{escape(daily.lead_paragraph)}</p>",
    ]
    for section in daily.sections:
        blocks.append(f"<h3 style='color:#e23e78'>{escape(section.label)}</h3>")
        for story in section.stories:
            blocks.append(f"<h4>{escape(story.title)}</h4><p>{escape(story.summary)}</p><p>{escape(story.source_name)}</p>")
    blocks.append("<footer>内部传阅</footer></article></body></html>")
    return "".join(blocks)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_html.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/html.py tests/test_html.py
git commit -m "feat: render the daily print page"
```

---

### Task 4: Accept one screenshot

**Files:**
- Create: `src/ai_daily/shot.py`
- Test: `tests/test_shot.py`

**Interfaces:**
- Consumes: PNG bytes
- Produces: `MAX_IMAGE_BYTES = 2_097_152`; `accept_image(png: bytes) -> bytes`; `screenshot_html(html: str) -> bytes`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from ai_daily.shot import MAX_IMAGE_BYTES, accept_image

def test_accepts_a_small_png():
    png = b"\x89PNG" + b"ok"
    assert accept_image(png) == png

def test_rejects_a_broken_or_oversized_image():
    with pytest.raises(RuntimeError):
        accept_image(b"not-a-png")
    with pytest.raises(RuntimeError):
        accept_image(b"\x89PNG" + b"x" * MAX_IMAGE_BYTES)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_shot.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

```python
MAX_IMAGE_BYTES = 2_097_152

def accept_image(png: bytes) -> bytes:
    if not png.startswith(b"\x89PNG") or len(png) > MAX_IMAGE_BYTES:
        raise RuntimeError("image rejected")
    return png

def screenshot_html(html: str) -> bytes:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 720, "height": 1280})
        page.set_content(html, wait_until="load")
        png = page.screenshot(full_page=True, type="png")
        browser.close()
    return accept_image(png)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_shot.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/shot.py tests/test_shot.py
git commit -m "feat: accept one poster screenshot"
```

---

### Task 5: WeCom image post and sent-date file

**Files:**
- Create: `src/ai_daily/wecom.py`
- Create: `src/ai_daily/state.py`
- Test: `tests/test_wecom.py`
- Test: `tests/test_state.py`

**Interfaces:**
- Consumes: PNG bytes, `date`, `Path`
- Produces: `image_body(png: bytes) -> dict`; `post_image(png: bytes, post) -> None`; `already_sent(path: Path, day: date) -> bool`; `mark_sent(path: Path, day: date) -> None`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_wecom.py
import base64, hashlib
from ai_daily.wecom import image_body, post_image

def test_image_body_is_one_image_and_not_a_link_message():
    png = b"\x89PNG-fake"
    body = image_body(png)
    assert body == {
        "msgtype": "image",
        "image": {
            "base64": base64.b64encode(png).decode(),
            "md5": hashlib.md5(png).hexdigest(),
        },
    }

def test_post_image_refuses_a_non_ok_response():
    def post(json):
        return {"errcode": 93000, "errmsg": "invalid"}
    try:
        post_image(b"\x89PNG", post)
        assert False
    except RuntimeError:
        pass
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

```python
# src/ai_daily/wecom.py
import base64, hashlib

def image_body(png: bytes) -> dict:
    return {
        "msgtype": "image",
        "image": {
            "base64": base64.b64encode(png).decode(),
            "md5": hashlib.md5(png).hexdigest(),
        },
    }

def post_image(png: bytes, post) -> None:
    body = post(image_body(png))
    if body.get("errcode") != 0:
        raise RuntimeError(body.get("errmsg") or "wecom rejected")
```

```python
# src/ai_daily/state.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_wecom.py tests/test_state.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/wecom.py src/ai_daily/state.py tests/test_wecom.py tests/test_state.py
git commit -m "feat: send one image and record the day"
```

---

### Task 6: run_once

**Files:**
- Create: `src/ai_daily/run.py`
- Test: `tests/test_run.py`

**Interfaces:**
- Consumes: `already_sent`, `mark_sent`, `parse_daily`, `render_html`, `accept_image`, `post_image`, `DailyNotReady`
- Produces: `run_once(day, state_path, payload, payload_error, shoot, post) -> str` returning `already-sent`, `not-ready`, `sent`, or `delivery-failed`

`shoot` is `Callable[[str], bytes]`. It receives the HTML and returns a PNG. `run_once` still passes that PNG through `accept_image` before posting.

- [ ] **Step 1: Write the failing test**

```python
from datetime import date
from pathlib import Path
from ai_daily.run import run_once
from ai_daily.state import already_sent, mark_sent

DAY = date(2026, 10, 21)
PAYLOAD = {
    "report": {
        "date": "2026-10-21",
        "lead": {"title": "DeepSeek 开源 DeepInfer", "leadParagraph": "同步开源。"},
        "sections": [{"label": "论文研究", "items": [{"title": "一篇论文", "summary": "一句。", "source": {"name": "HF"}}]}],
        "flashes": [{"title": "快讯不该进图"}],
    }
}

def test_already_sent_does_not_shoot(tmp_path: Path):
    mark_sent(tmp_path / "sent.json", DAY)
    assert run_once(DAY, tmp_path / "sent.json", PAYLOAD, None, lambda html: b"\x89PNG", lambda json: {"errcode": 0}) == "already-sent"

def test_not_ready_does_not_mark_sent(tmp_path: Path):
    path = tmp_path / "sent.json"
    result = run_once(DAY, path, {}, RuntimeError("404"), lambda html: b"\x89PNG", lambda json: {"errcode": 0})
    assert result == "not-ready"
    assert already_sent(path, DAY) is False

def test_oversized_image_does_not_post_or_mark_sent(tmp_path: Path):
    path = tmp_path / "sent.json"
    posts = []
    result = run_once(DAY, path, PAYLOAD, None, lambda html: b"\x89PNG" + b"x" * 3_000_000, lambda json: posts.append(json))
    assert result == "delivery-failed"
    assert posts == []
    assert already_sent(path, DAY) is False

def test_webhook_failure_does_not_mark_sent(tmp_path: Path):
    path = tmp_path / "sent.json"
    result = run_once(DAY, path, PAYLOAD, None, lambda html: b"\x89PNG-ok", lambda json: {"errcode": 1, "errmsg": "no"})
    assert result == "delivery-failed"
    assert already_sent(path, DAY) is False

def test_success_posts_one_image_and_marks_sent(tmp_path: Path):
    path = tmp_path / "sent.json"
    seen = []
    def shoot(html):
        seen.append(html)
        return b"\x89PNG-ok"
    posts = []
    result = run_once(DAY, path, PAYLOAD, None, shoot, lambda json: posts.append(json) or {"errcode": 0})
    assert result == "sent"
    assert "快讯不该进图" not in seen[0]
    assert posts[0]["msgtype"] == "image"
    assert already_sent(path, DAY) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_run.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

```python
from datetime import date
from pathlib import Path
from ai_daily.aihot import DailyNotReady, parse_daily
from ai_daily.html import render_html
from ai_daily.shot import accept_image
from ai_daily.state import already_sent, mark_sent
from ai_daily.wecom import post_image

def run_once(day: date, state_path: Path, payload: dict, payload_error: Exception | None, shoot, post) -> str:
    if already_sent(state_path, day):
        return "already-sent"
    if payload_error is not None:
        return "not-ready"
    try:
        daily = parse_daily(payload, day)
    except DailyNotReady:
        return "not-ready"
    try:
        png = accept_image(shoot(render_html(daily)))
    except Exception:
        return "delivery-failed"
    try:
        post_image(png, post)
    except Exception:
        return "delivery-failed"
    mark_sent(state_path, day)
    return "sent"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_run.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/run.py tests/test_run.py
git commit -m "feat: close the day only after a sent screenshot"
```

---

### Task 7: Command entry

**Files:**
- Create: `src/ai_daily/__main__.py`
- Test: `tests/test_main.py`

**Interfaces:**
- Consumes: `run_once`, `beijing_date`, `screenshot_html`, httpx
- Produces: `main(argv: list[str], environ: dict, now, get, shoot, post) -> int`

- [ ] **Step 1: Write the failing test**

```python
from datetime import datetime, timezone
from ai_daily.__main__ import main

def test_missing_webhook_exits_without_getting_or_posting():
    calls = []
    code = main([], {}, datetime(2026, 10, 21, 1, tzinfo=timezone.utc), lambda url: calls.append(url), lambda html: b"\x89PNG", lambda url, json: calls.append(url))
    assert code == 2
    assert calls == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_main.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

```python
from datetime import datetime
from pathlib import Path
from ai_daily.dates import beijing_date
from ai_daily.run import run_once

def main(argv: list[str], environ: dict, now: datetime, get, shoot, post) -> int:
    webhook = environ.get("WECOM_WEBHOOK_URL")
    if not webhook:
        return 2
    day = beijing_date(now)
    url = f"https://aihot.news/api/v1/dailies/{day.isoformat()}"
    try:
        payload = get(url)
        payload_error = None
    except Exception as exc:
        payload = {}
        payload_error = exc
    result = run_once(day, Path(environ.get("AI_DAILY_STATE_PATH", "data/sent.json")), payload, payload_error, shoot, lambda body: post(webhook, body))
    print(result)
    return 0 if result in {"sent", "already-sent"} else 1
```

`python -m ai_daily` calls `main` with `os.environ`, `datetime.now(timezone.utc)`, an httpx GET that returns `response.json()`, `screenshot_html`, and an httpx POST to the webhook URL that returns `response.json()`. Do not print the webhook URL.

- [ ] **Step 4: Run the full test suite**

Run: `python -m pytest -v`
Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/ai_daily/__main__.py tests/test_main.py
git commit -m "feat: add the daily screenshot command"
```
