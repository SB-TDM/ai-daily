import base64
import re
from io import BytesIO
from urllib.parse import urljoin

_IMG = re.compile(r"<img\b[^>]*>", re.I)
_SRC = re.compile(r"""src\s*=\s*['"]([^'"]+)['"]""", re.I)
_OG = re.compile(r"""<meta\b[^>]*property\s*=\s*['"]og:image['"][^>]*>""", re.I)
_CONTENT = re.compile(r"""content\s*=\s*['"]([^'"]+)['"]""", re.I)


def _skip(src: str) -> bool:
    low = src.lower()
    return low.startswith("data:") or "beian" in low or "favicon" in low


def first_image_url(html: str, origin: str) -> str | None:
    for tag in _IMG.findall(html):
        match = _SRC.search(tag)
        if not match:
            continue
        src = match.group(1).strip()
        if _skip(src) or "/api/img-proxy" not in src:
            continue
        return urljoin(origin, src)
    for tag in _OG.findall(html):
        match = _CONTENT.search(tag)
        if not match or _skip(match.group(1)):
            continue
        return match.group(1).strip()
    return None


def shrink_image(raw: bytes, *, wide: int) -> str:
    from PIL import Image

    image = Image.open(BytesIO(raw)).convert("RGB")
    image.thumbnail((wide, 480 if wide > 160 else 120))
    buf = BytesIO()
    image.save(buf, format="JPEG", quality=72 if wide > 160 else 70)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def load_story_images(daily, get_text, get_bytes, origin: str = "https://aihot.news") -> dict[str, str]:
    found = {}
    for section in daily.sections:
        for story in section.stories:
            url = story.page_url
            if not url or url in found:
                continue
            try:
                image_url = first_image_url(get_text(url), origin)
                if not image_url:
                    continue
                wide = 720 if story.title == daily.lead_title else 160
                found[url] = shrink_image(get_bytes(image_url), wide=wide)
            except Exception:
                continue
    return found
