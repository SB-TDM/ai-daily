import base64, hashlib
from ai_daily.wecom import image_body, post_image

def test_image_body_is_one_image_and_not_a_link_message():
    png = b"\x89PNG-fake"
    body = image_body(png)
    assert body == {
        "msgtype": "image",
        "image": {
            "base64": base64.b64encode(png).decode(),
            "md5": hashlib.md5(png).hexdigest(),
        },
    }

def test_post_image_refuses_a_non_ok_response():
    def post(json):
        return {"errcode": 93000, "errmsg": "invalid"}
    try:
        post_image(b"\x89PNG", post)
        assert False
    except RuntimeError:
        pass
