import base64, hashlib

def image_body(png: bytes) -> dict:
    return {
        "msgtype": "image",
        "image": {
            "base64": base64.b64encode(png).decode(),
            "md5": hashlib.md5(png).hexdigest(),
        },
    }

def post_image(png: bytes, post) -> None:
    body = post(image_body(png))
    if body.get("errcode") != 0:
        raise RuntimeError(body.get("errmsg") or "wecom rejected")
