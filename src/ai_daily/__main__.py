from datetime import datetime, timezone
from pathlib import Path
import os
import sys
from ai_daily.dates import beijing_date
from ai_daily.run import run_once
from ai_daily.shot import screenshot_html

def main(argv: list[str], environ: dict, now: datetime, get, shoot, post, load_images=None) -> int:
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
    result = run_once(day, Path(environ.get("AI_DAILY_STATE_PATH", "data/sent.json")), payload, payload_error, shoot, lambda body: post(webhook, body), load_images)
    print(result)
    return 0 if result in {"sent", "already-sent"} else 1

def _get(url: str):
    import httpx
    return httpx.get(url).json()

def _post(url: str, body):
    import httpx
    return httpx.post(url, json=body).json()

def _load_images(daily):
    import httpx
    from ai_daily.images import load_story_images

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}

    def get_text(url: str) -> str:
        return httpx.get(url, timeout=8, follow_redirects=True, headers=headers).text

    def get_bytes(url: str) -> bytes:
        return httpx.get(url, timeout=8, follow_redirects=True, headers=headers).content

    return load_story_images(daily, get_text, get_bytes)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:], os.environ, datetime.now(timezone.utc), _get, screenshot_html, _post, _load_images))
