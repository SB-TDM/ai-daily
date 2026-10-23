"""A per-run immutable configuration snapshot; no credentials in representations."""
from dataclasses import dataclass, field
import json
from pathlib import Path
from urllib.parse import urlsplit

from .storage import read_json


@dataclass(frozen=True)
class ImageSettings:
    model: str = ""
    base_url: str = field(default="", repr=False)
    key: str = field(default="", repr=False)
    _extra: str = field(default="{}", repr=False)
    _scenes: str = field(default="{}", repr=False)

    @property
    def extra(self):
        return json.loads(self._extra)

    @property
    def scenes(self):
        return json.loads(self._scenes)

    @property
    def ready(self):
        try:
            parsed = urlsplit(self.base_url)
            return bool(self.model and self.key and parsed.scheme in ("http", "https")
                        and parsed.hostname and not parsed.username and not parsed.password
                        and not parsed.query and not parsed.fragment)
        except ValueError:
            return False


def load_image_settings(root):
    data = Path(root) / "data"
    image, secret = read_json(data / "image.json", {}), read_json(data / "image-secret.json", {})
    scenes = read_json(data / "image-scenes.json", {})
    image = image if isinstance(image, dict) else {}
    secret = secret if isinstance(secret, dict) else {}
    scenes = {k: v for k, v in scenes.items() if isinstance(v, str) and v.strip()} if isinstance(scenes, dict) else {}
    reserved = {"model", "base_url", "extra", "key", "api_key", "password", "authorization", "headers"}
    extra = {k: v for k, v in image.items() if k.lower() not in reserved}
    nested = image.get("extra")
    if isinstance(nested, dict):
        extra.update({k: v for k, v in nested.items() if k.lower() not in reserved})
    def text(value):
        return value.strip() if isinstance(value, str) else ""
    return ImageSettings(text(image.get("model")), text(image.get("base_url")).rstrip("/"),
                         text(secret.get("key")), json.dumps(extra, sort_keys=True), json.dumps(scenes, sort_keys=True))
