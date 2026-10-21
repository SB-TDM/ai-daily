from datetime import date
from pathlib import Path
from ai_daily.aihot import DailyNotReady, parse_daily
from ai_daily.html import render_html
from ai_daily.shot import accept_image
from ai_daily.state import already_sent, mark_sent
from ai_daily.wecom import post_image

def run_once(day: date, state_path: Path, payload: dict, payload_error: Exception | None, shoot, post, load_images=None) -> str:
    if already_sent(state_path, day):
        return "already-sent"
    if payload_error is not None:
        return "not-ready"
    try:
        daily = parse_daily(payload, day)
    except DailyNotReady:
        return "not-ready"
    images = {}
    if load_images is not None:
        try:
            images = load_images(daily) or {}
        except Exception:
            images = {}
    try:
        png = accept_image(shoot(render_html(daily, images)))
    except Exception:
        return "delivery-failed"
    try:
        post_image(png, post)
    except Exception:
        return "delivery-failed"
    mark_sent(state_path, day)
    return "sent"
