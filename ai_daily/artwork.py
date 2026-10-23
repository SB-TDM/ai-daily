"""Wordless image requests and validated, collision-resistant local image caching."""
import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path
import urllib.request

from PIL import Image

from .report import item_key
from .storage import atomic_write

PROMPT_VERSION = "wordless-scene-v2"


def illustration_prompt(title, summary, *, scene=None):
    subject = scene if scene is not None else title + ". " + (summary or "")
    return (
        "A single wordless editorial scene for a printed newspaper. Flat ink, muted teal, "
        "ochre and navy on warm cream newsprint. Tell the story only with physical objects "
        "and their arrangement. No infographic, panels, charts, statistics, interface, code, "
        "labels, writing, letters, numbers, punctuation, watermarks or brand logos anywhere. "
        "No real person's likeness. Any paper, equipment or clothing must be completely "
        "unmarked. Never reproduce names, acronyms or quantities from the context. Scene: "
        + subject + ". Render only the scene; every surface stays free of text and emblems."
    )


def read_image(raw):
    try:
        with Image.open(BytesIO(raw)) as image:
            image.load()
            return image.convert("RGB")
    except Exception:
        raise ValueError("Invalid illustration bytes") from None


def request_image(settings, title, summary, *, scene=None, opener=None):
    if not settings.ready:
        raise ValueError("Image settings unavailable")
    base = settings.base_url.rstrip("/")
    endpoint = base + ("/images/generations" if base.endswith("/v1") else "/v1/images/generations")
    body = {"size": "1024x1024", **settings.extra, "model": settings.model,
            "prompt": illustration_prompt(title, summary, scene=scene), "n": 1, "response_format": "b64_json"}
    request = urllib.request.Request(endpoint, data=json.dumps(body).encode("utf-8"),
                                     headers={"Authorization": "Bearer " + settings.key, "Content-Type": "application/json"})
    with (opener or urllib.request.urlopen)(request, timeout=240) as response:
        payload = json.loads(response.read().decode("utf-8"))
    raw = base64.b64decode(payload["data"][0]["b64_json"], validate=True)
    read_image(raw)
    return raw


def cache_key(settings, item, *, scene=None):
    identity = {"version": PROMPT_VERSION, "story": item_key(item), "title": item.get("title", ""),
                "summary": item.get("summary") or "", "scene": scene, "model": settings.model,
                "base_url": settings.base_url.rstrip("/"), "extra": settings.extra}
    return hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def artwork_path(root, settings, item, *, scene=None):
    return Path(root) / "data" / "artwork" / (cache_key(settings, item, scene=scene) + ".png")


def store_artwork(root, settings, item, raw, *, scene=None):
    picture = read_image(raw)
    buffer = BytesIO()
    picture.save(buffer, format="PNG")
    atomic_write(artwork_path(root, settings, item, scene=scene), buffer.getvalue())
    return picture


def load_artwork(root, settings, item, *, offline=False, fetch_image=None):
    scene = settings.scenes.get(item_key(item))
    path = artwork_path(root, settings, item, scene=scene)
    try:
        return read_image(path.read_bytes())
    except (OSError, ValueError):
        pass
    if offline or not settings.ready:
        return None
    raw = (fetch_image or request_image)(settings, item["title"], item.get("summary") or "", scene=scene)
    return store_artwork(root, settings, item, raw, scene=scene)
