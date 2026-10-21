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
    import base64
    import httpx
    from ai_daily.images import illustrate_first, illustration_prompt

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return {}
    base = os.environ.get("OPENAI_BASE_URL", "https://www.string.ink/v1").rstrip("/")

    def generate(title: str, summary: str) -> bytes:
        last = None
        for attempt in range(3):
            try:
                response = httpx.post(
                    f"{base}/images/generations",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "model": "grok-imagine-image",
                        "prompt": illustration_prompt(title, summary),
                        "n": 1,
                        "size": "1024x1024",
                        "response_format": "b64_json",
                    },
                    timeout=120,
                )
                response.raise_for_status()
                return base64.b64decode(response.json()["data"][0]["b64_json"])
            except Exception as exc:
                last = exc
                if attempt < 2:
                    import time
                    time.sleep(2)
        raise last

    return illustrate_first(daily, generate)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:], os.environ, datetime.now(timezone.utc), _get, screenshot_html, _post, _load_images))
