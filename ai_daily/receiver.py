"""Accept one WeCom callback, answer it, and exit the image tool when finished."""
from dataclasses import dataclass
import json
from pathlib import Path
from urllib.parse import urlsplit
import urllib.request

from .commands import handle_command
from .dates import beijing_date
from .generate import generate_poster, poster_ready
from .settings import load_image_settings
from .storage import GenerationBusy, generation_lock, read_json, write_json
from .wecom import CryptoError, command_text, decrypt, encrypted_envelope, image_body, missing_credential, sign

DONE = "做好啦，图在上面。要发到群里就说发送"
NOT_SENT = "没发到群里，再说一次发送吧"
NOT_READY = "今天的日报还没出来，我做不了"


@dataclass(frozen=True)
class Handled:
    reply: str
    follow: object = None
    duplicate: bool = False


def _seen_path(root):
    return Path(root) / "data" / "seen-msgids.json"


def claim_msgid(root, msgid):
    if not msgid:
        return True
    path = _seen_path(root)
    seen = read_json(path, [])
    if not isinstance(seen, list):
        seen = []
    if msgid in seen:
        return False
    write_json(path, [*seen, msgid][-500:])
    return True


def generating(root):
    try:
        with generation_lock(root):
            return False
    except GenerationBusy:
        return True


def _save_decision(root, decision):
    data = Path(root) / "data"
    if decision.schedule:
        write_json(data / "schedule.json", {"time": decision.schedule})
    if decision.image_patch:
        current = read_json(data / "image.json", {})
        if not isinstance(current, dict):
            current = {}
        current.update(decision.image_patch)
        write_json(data / "image.json", current)
    if decision.secret is not None:
        write_json(data / "image-secret.json", {"key": decision.secret})


def _allowed(url):
    parsed = urlsplit(url or "")
    return parsed.scheme == "https" and parsed.hostname == "qyapi.weixin.qq.com"


def handle_event(message, *, root, post_image, post_text, generate=None, reply=None, preview=None):
    root = Path(root)
    msgid = message.get("msgid") or ""
    if not claim_msgid(root, msgid):
        return Handled("", duplicate=True)
    content = ((message.get("text") or {}).get("content")) or ""
    day = beijing_date()
    path = root / "data" / "posters" / f"{day.isoformat()}.png"
    settings = load_image_settings(root)
    decision = handle_command(
        command_text(content),
        generating=generating(root),
        poster_ready=poster_ready(path),
        image={"model": settings.model, "base_url": settings.base_url},
    )
    _save_decision(root, decision)
    response_url = message.get("response_url") or ""
    if decision.send:
        ok = post_image(path)
        return Handled("发到群里啦" if ok else NOT_SENT)

    def follow(force):
        result = (generate or generate_poster)(root, force=force)
        text = DONE if result.status in ("ready", "already_ready") else "还在做呢，等我一下" if result.status == "busy" else NOT_READY
        if reply:
            reply(text)
        elif _allowed(response_url):
            post_text(response_url, text)
        poster = getattr(result, "path", None)
        if preview and result.status in ("ready", "already_ready") and poster and Path(poster).is_file():
            preview(Path(poster).read_bytes())

    if decision.start_tool:
        force = command_text(content) == "重新生成"
        return Handled(decision.reply, follow=lambda: follow(force))
    return Handled(decision.reply)


def handle_frame(frame, *, root, post_image, reply, preview=None, generate=None):
    body = frame.get("body") or {}
    message = {"msgid": body.get("msgid") or "", "text": body.get("text") or {}}
    handled = handle_event(
        message,
        root=root,
        post_image=post_image,
        post_text=lambda url, text: None,
        generate=generate,
        reply=reply,
        preview=preview,
    )
    if handled.reply:
        reply(handled.reply)
    return handled


def _env(root):
    values = {}
    path = Path(root) / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.strip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"')
    return values


def serve_long(root, client_factory):
    env = _env(root)
    missing = missing_credential(env)
    if missing:
        print(missing)
        return 2
    client = client_factory({
        "bot_id": env["WECOM_BOT_ID"],
        "secret": env["WECOM_BOT_SECRET"],
        "max_reconnect_attempts": -1,
    })
    webhook = env["WECOM_WEBHOOK_URL"]

    def on_text(frame):
        def reply(text):
            sender = getattr(client, "reply_text", None)
            if sender:
                sender(frame, text)

        def preview(png):
            sender = getattr(client, "preview_image", None)
            if sender:
                sender(frame, png)

        def post_image(path):
            if not Path(path).exists():
                return False
            return post_webhook_image(webhook, Path(path).read_bytes())

        handled = handle_frame(
            frame, root=root, post_image=post_image, reply=reply, preview=preview,
        )
        if handled.follow:
            import threading
            threading.Thread(target=handled.follow, daemon=True).start()

    client.on("message.text", on_text)
    client.connect()
    return 0


def verify_echo(query, token, aes_key):
    if sign(token, query.get("timestamp"), query.get("nonce"), query.get("echostr")) != query.get("msg_signature"):
        raise CryptoError("bad signature")
    plain, _ = decrypt(aes_key, query.get("echostr"))
    return plain


def open_callback(body, query, token, aes_key):
    payload = json.loads(body)
    encrypted = payload.get("encrypt") or ""
    if sign(token, query.get("timestamp"), query.get("nonce"), encrypted) != query.get("msg_signature"):
        raise CryptoError("bad signature")
    plain, _ = decrypt(aes_key, encrypted)
    return json.loads(plain)


def post_webhook_image(url, png, opener=None):
    if not _allowed(url):
        return False
    request = urllib.request.Request(
        url,
        data=json.dumps(image_body(png)).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with (opener or urllib.request.urlopen)(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return False
    return payload.get("errcode") == 0


def post_response_text(url, text, opener=None):
    if not _allowed(url):
        return
    request = urllib.request.Request(
        url,
        data=json.dumps({"msgtype": "text", "text": {"content": text}}, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with (opener or urllib.request.urlopen)(request, timeout=30) as response:
        response.read()


def callback_response(method, query, body, *, token, aes_key, root, post_image, post_text):
    try:
        if method == "GET":
            plain = verify_echo(query, token, aes_key)
            return 200, plain.encode("utf-8"), "text/plain", None
        message = open_callback(body, query, token, aes_key)
    except (CryptoError, ValueError, KeyError):
        return 403, b"", "text/plain", None
    handled = handle_event(message, root=root, post_image=post_image, post_text=post_text)
    if handled.duplicate or not handled.reply:
        return 200, b"", "text/plain", None
    payload = json.dumps(encrypted_envelope(token, aes_key, handled.reply), ensure_ascii=False).encode("utf-8")
    return 200, payload, "application/json", handled.follow
