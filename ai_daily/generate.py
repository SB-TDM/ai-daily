"""On-demand newspaper generation. This module has no delivery operation."""
from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
import urllib.error
import urllib.request

from PIL import Image

from .artwork import load_artwork
from .dates import beijing_date
from .render import MAX_BYTES, fit_png, render_poster
from .report import ReportNotReady, first_items, item_key, validate_report
from .settings import load_image_settings
from .storage import GenerationBusy, atomic_write, generation_lock, read_json, write_json

DAILY_URL = "https://aihot.news/api/v1/dailies/latest"


@dataclass(frozen=True)
class GenerationResult:
    status: str
    path: Path | None = None
    illustrations: int = 0
    expected_illustrations: int = 0
    reason: str | None = None


def fetch_daily(etag=None):
    headers = {"Accept": "application/json"}
    if etag:
        headers["If-None-Match"] = etag
    request = urllib.request.Request(DAILY_URL, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
            tag = response.headers.get("ETag")
            return status, tag, json.loads(response.read().decode("utf-8")) if status == 200 else None
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return 304, exc.headers.get("ETag"), None
        raise


def poster_ready(path):
    try:
        path = Path(path)
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            return False
        with Image.open(BytesIO(path.read_bytes())) as image:
            image.load()
            return image.format == "PNG" and image.width > 0 and image.height > 0
    except (OSError, ValueError, Image.DecompressionBombError):
        return False


def _daily(root, day, supplied, offline, fetcher):
    cache_path = root / "data" / "daily-cache.json"
    cached = read_json(cache_path, {})
    cached = cached if isinstance(cached, dict) else {}
    if supplied is not None:
        return validate_report(supplied, day)
    if offline:
        return validate_report(cached.get("report"), day)
    etag = cached.get("etag")
    if not isinstance(etag, str):
        etag = None
    status, tag, payload = fetcher(etag)
    if status == 304:
        return validate_report(cached.get("report"), day)
    if status != 200:
        raise ReportNotReady("Daily request was unsuccessful")
    report = validate_report(payload, day)
    write_json(cache_path, {"etag": tag if isinstance(tag, str) else None, "report": report})
    return report


def generate_poster(root, *, force=False, now=None, report=None, offline=False, fetch_daily=None, fetch_image=None):
    root = Path(root)
    stage = "storage"
    try:
        day = beijing_date(now)
        output = root / "data" / "posters" / f"{day.isoformat()}.png"
        with generation_lock(root):
            if not force and poster_ready(output):
                return GenerationResult("already_ready", output)
            settings = load_image_settings(root)
            stage = "report"
            daily = _daily(root, day, report, offline, fetch_daily or globals()["fetch_daily"])
            targets = first_items(daily)
            pictures = {}
            for item in targets:
                try:
                    picture = load_artwork(root, settings, item, offline=offline, fetch_image=fetch_image)
                    if picture is not None:
                        pictures[item_key(item)] = picture
                except Exception:
                    # A missing illustration must never drop the rest of the report.
                    # Do not expose network exception text, which can contain credentials.
                    continue
            stage = "render"
            png = fit_png(render_poster(daily, pictures))
            stage = "storage"
            atomic_write(output, png)
            return GenerationResult("ready", output, len(pictures), len(targets))
    except GenerationBusy:
        return GenerationResult("busy")
    except Exception:
        return GenerationResult("not_ready", reason=stage)
