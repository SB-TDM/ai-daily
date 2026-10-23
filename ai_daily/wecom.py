"""WeCom callback crypto and the already-tested image webhook body. No network here."""
import base64
import hashlib
import json
import os
import struct
import time
import secrets

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

BLOCK = 32


class CryptoError(ValueError):
    pass


def sign(token, timestamp, nonce, encrypt):
    parts = sorted(str(part) for part in (token, timestamp, nonce, encrypt))
    return hashlib.sha1("".join(parts).encode("utf-8")).hexdigest()


def _aes_key(encoding_aes_key):
    try:
        key = base64.b64decode(encoding_aes_key + "=", validate=True)
    except Exception:
        raise CryptoError("bad aes key") from None
    if len(key) != 32:
        raise CryptoError("bad aes key")
    return key


def _pad(data):
    pad = BLOCK - (len(data) % BLOCK)
    return data + bytes([pad]) * pad


def _unpad(data):
    pad = data[-1]
    if pad < 1 or pad > BLOCK or data[-pad:] != bytes([pad]) * pad:
        raise CryptoError("bad padding")
    return data[:-pad]


def encrypt(encoding_aes_key, text, receiveid=""):
    key = _aes_key(encoding_aes_key)
    raw = os.urandom(16) + struct.pack(">I", len(text.encode("utf-8"))) + text.encode("utf-8") + receiveid.encode("utf-8")
    cipher = Cipher(algorithms.AES(key), modes.CBC(key[:16])).encryptor()
    return base64.b64encode(cipher.update(_pad(raw)) + cipher.finalize()).decode("ascii")


def decrypt(encoding_aes_key, encrypted):
    key = _aes_key(encoding_aes_key)
    try:
        raw = base64.b64decode(encrypted, validate=True)
        cipher = Cipher(algorithms.AES(key), modes.CBC(key[:16])).decryptor()
        plain = _unpad(cipher.update(raw) + cipher.finalize())
        length = struct.unpack(">I", plain[16:20])[0]
        message = plain[20:20 + length].decode("utf-8")
        receiveid = plain[20 + length:].decode("utf-8")
    except CryptoError:
        raise
    except Exception:
        raise CryptoError("bad message") from None
    return message, receiveid


def command_text(content):
    text = (content or "").strip()
    if text.startswith("@"):
        return text.split(maxsplit=1)[1].strip() if " " in text else ""
    return text


def image_body(png):
    return {
        "msgtype": "image",
        "image": {
            "base64": base64.b64encode(png).decode("ascii"),
            "md5": hashlib.md5(png).hexdigest(),
        },
    }


def passive_reply(text):
    return {"msgtype": "stream", "stream": {"id": secrets.token_hex(8), "finish": True, "content": text}}


def encrypted_envelope(token, encoding_aes_key, text):
    encrypted = encrypt(encoding_aes_key, json.dumps(passive_reply(text), ensure_ascii=False))
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(8)
    return {
        "encrypt": encrypted,
        "msgsignature": sign(token, timestamp, nonce, encrypted),
        "timestamp": timestamp,
        "nonce": nonce,
    }


def missing_credential(env):
    for name in ("WECOM_BOT_ID", "WECOM_BOT_SECRET", "WECOM_WEBHOOK_URL"):
        if not (env.get(name) or "").strip():
            return f"缺少 {name}"
    return None
