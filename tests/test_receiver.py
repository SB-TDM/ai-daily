import base64
import hashlib
import json
from datetime import date
from io import BytesIO

from PIL import Image

from ai_daily.receiver import handle_event, handle_frame, open_callback, verify_echo
from ai_daily.wecom import encrypt, image_body, missing_credential, sign

TOKEN = "token"
AES = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG"


def png():
    buffer = BytesIO()
    Image.new("RGB", (2, 2), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def message(text, msgid="m1", response_url="https://qyapi.weixin.qq.com/cgi-bin/aibot/response?response_code=1"):
    return {"msgid": msgid, "msgtype": "text", "text": {"content": text}, "response_url": response_url}


def test_round_trip_and_url_verification():
    encrypted = encrypt(AES, "echo-ok", "")
    query = {"timestamp": "1", "nonce": "n", "echostr": encrypted, "msg_signature": sign(TOKEN, "1", "n", encrypted)}
    assert verify_echo(query, TOKEN, AES) == "echo-ok"
    query["msg_signature"] = "bad"
    try:
        verify_echo(query, TOKEN, AES)
    except Exception as exc:
        assert type(exc).__name__ == "CryptoError"
    else:
        raise AssertionError("bad signature accepted")


def test_generate_replies_now_and_finishes_on_response_url_without_webhook(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_daily.receiver.beijing_date", lambda now=None: date(2026, 10, 23))
    calls = []

    def generate(root, force=False):
        calls.append(("generate", force))
        return type("R", (), {"status": "ready"})()

    handled = handle_event(
        message("@日报机器人 生成日报"),
        root=tmp_path,
        post_image=lambda path: calls.append("webhook") or True,
        post_text=lambda url, text: calls.append(("text", text, "qyapi" in url)),
        generate=generate,
    )
    assert handled.reply == "好，我去做今天的日报啦"
    assert calls == []
    handled.follow()
    assert calls == [("generate", False), ("text", "做好啦，图在上面。要发到群里就说发送", True)]


def test_failed_generate_does_not_send_image(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_daily.receiver.beijing_date", lambda now=None: date(2026, 10, 23))
    calls = []
    handled = handle_event(
        message("重新生成", "m2"),
        root=tmp_path,
        post_image=lambda path: calls.append("webhook") or False,
        post_text=lambda url, text: calls.append(text),
        generate=lambda root, force=False: type("R", (), {"status": "not_ready"})(),
    )
    handled.follow()
    assert calls == ["今天的日报还没出来，我做不了"]


def test_send_posts_image_and_does_not_use_response_url(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_daily.receiver.beijing_date", lambda now=None: date(2026, 10, 23))
    path = tmp_path / "data" / "posters" / "2026-10-23.png"
    path.parent.mkdir(parents=True)
    raw = png()
    path.write_bytes(raw)
    seen = []
    handled = handle_event(
        message("@机器人 发送", "m3"),
        root=tmp_path,
        post_image=lambda poster: seen.append(poster.read_bytes()) or True,
        post_text=lambda url, text: seen.append(url),
    )
    assert handled.reply == "发到群里啦"
    assert handled.follow is None
    assert seen == [raw]


def test_rejected_webhook_says_not_sent(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_daily.receiver.beijing_date", lambda now=None: date(2026, 10, 23))
    path = tmp_path / "data" / "posters" / "2026-10-23.png"
    path.parent.mkdir(parents=True)
    path.write_bytes(png())
    handled = handle_event(message("发送", "m4"), root=tmp_path, post_image=lambda poster: False, post_text=lambda *args: None)
    assert handled.reply == "没发到群里，再说一次发送吧"


def test_duplicate_msgid_does_not_generate_or_send(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_daily.receiver.beijing_date", lambda now=None: date(2026, 10, 23))
    calls = []
    kwargs = dict(root=tmp_path, post_image=lambda path: calls.append("send"), post_text=lambda *args: calls.append(args), generate=lambda *args, **kw: calls.append("gen"))
    first = handle_event(message("生成日报", "same"), **kwargs)
    second = handle_event(message("生成日报", "same"), **kwargs)
    assert first.reply == "好，我去做今天的日报啦"
    assert second.duplicate is True
    assert calls == []


def test_secret_is_saved_but_not_replied(tmp_path):
    handled = handle_event(message("参数 密钥 hidden-value", "m5"), root=tmp_path, post_image=lambda path: False, post_text=lambda *args: None)
    saved = json.loads((tmp_path / "data" / "image-secret.json").read_text(encoding="utf-8"))
    assert handled.reply == "改好啦"
    assert "hidden-value" not in handled.reply
    assert saved == {"key": "hidden-value"}


def test_callback_decrypts_signed_json():
    payload = {"msgid": "m", "text": {"content": "发送"}}
    encrypted = encrypt(AES, json.dumps(payload), "")
    query = {"timestamp": "9", "nonce": "abc", "msg_signature": sign(TOKEN, "9", "abc", encrypted)}
    assert open_callback(json.dumps({"encrypt": encrypted}), query, TOKEN, AES)["msgid"] == "m"


def test_image_body_uses_base64_and_md5():
    raw = b"png-bytes"
    body = image_body(raw)
    assert body["msgtype"] == "image"
    assert base64.b64decode(body["image"]["base64"]) == raw
    assert body["image"]["md5"] == hashlib.md5(raw).hexdigest()


def test_long_connection_replies_on_the_connection_and_not_the_webhook(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_daily.receiver.beijing_date", lambda now=None: date(2026, 10, 23))
    replies = []
    previews = []
    calls = []
    raw = png()
    frame = {"body": {"msgid": "m9", "text": {"content": "@日报机器人 生成日报"}}}

    def generate(root, force=False):
        calls.append(("generate", force))
        path = root / "data" / "posters" / "2026-10-23.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return type("R", (), {"status": "ready", "path": path})()

    handled = handle_frame(
        frame,
        root=tmp_path,
        post_image=lambda path: calls.append("webhook") or True,
        reply=replies.append,
        preview=previews.append,
        generate=generate,
    )
    assert replies == ["好，我去做今天的日报啦"]
    assert calls == []
    assert previews == []
    handled.follow()
    assert calls == [("generate", False)]
    assert replies == ["好，我去做今天的日报啦", "做好啦，图在上面。要发到群里就说发送"]
    assert previews == [raw]


def test_long_connection_send_uses_webhook_and_replies_sent(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_daily.receiver.beijing_date", lambda now=None: date(2026, 10, 23))
    path = tmp_path / "data" / "posters" / "2026-10-23.png"
    path.parent.mkdir(parents=True)
    raw = png()
    path.write_bytes(raw)
    replies = []
    seen = []
    frame = {"body": {"msgid": "m10", "text": {"content": "@机器人 发送"}}}
    handled = handle_frame(
        frame,
        root=tmp_path,
        post_image=lambda poster: seen.append(poster.read_bytes()) or True,
        reply=replies.append,
    )
    assert replies == ["发到群里啦"]
    assert seen == [raw]
    assert handled.follow is None


def test_serve_connects_out_with_bot_credentials(tmp_path, capsys):
    (tmp_path / ".env").write_text(
        "WECOM_BOT_ID=bot\nWECOM_BOT_SECRET=secret\nWECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=k\n",
        encoding="utf-8",
    )
    seen = {}

    class Fake:
        def on(self, event, handler):
            seen["event"] = event

        def connect(self):
            seen["connected"] = True

    def factory(options):
        seen["options"] = options
        return Fake()

    from ai_daily.receiver import serve_long

    assert serve_long(tmp_path, client_factory=factory) == 0
    assert seen["options"]["bot_id"] == "bot"
    assert seen["options"]["max_reconnect_attempts"] == -1
    assert seen["options"]["secret"] == "secret"
    assert seen["event"] == "message.text"
    assert seen["connected"] is True
    assert "secret" not in capsys.readouterr().out


def test_missing_credentials_are_named_without_values():
    assert missing_credential({}) == "缺少 WECOM_BOT_ID"
    assert missing_credential({"WECOM_BOT_ID": "id"}) == "缺少 WECOM_BOT_SECRET"
    assert missing_credential({"WECOM_BOT_ID": "id", "WECOM_BOT_SECRET": "secret"}) == "缺少 WECOM_WEBHOOK_URL"
    ready = {"WECOM_BOT_ID": "id", "WECOM_BOT_SECRET": "secret", "WECOM_WEBHOOK_URL": "https://qyapi.weixin.qq.com/hook"}
    assert missing_credential(ready) is None
    assert "secret" not in (missing_credential({"WECOM_BOT_ID": "id"}) or "")
