"""Send a finished poster back into the same WeCom chat."""
import asyncio
import base64
import hashlib
import math

CHUNK = 512 * 1024


async def send_chat_image(ws, frame, png, filename="daily.png"):
    media_id = await _upload_image(ws, png, filename)
    await ws.reply(frame, {"msgtype": "image", "image": {"media_id": media_id}})


async def _upload_image(ws, png, filename):
    if len(png) < 5:
        raise ValueError("image too small")
    chunks = math.ceil(len(png) / CHUNK)
    if chunks > 100:
        raise ValueError("image too large")
    init = await _exchange(ws, "aibot_upload_media_init", {
        "type": "image",
        "filename": filename,
        "total_size": len(png),
        "total_chunks": chunks,
        "md5": hashlib.md5(png).hexdigest(),
    })
    upload_id = (init.get("body") or {}).get("upload_id")
    if not upload_id:
        raise RuntimeError("upload rejected")
    for index in range(chunks):
        piece = png[index * CHUNK:(index + 1) * CHUNK]
        await _exchange(ws, "aibot_upload_media_chunk", {
            "upload_id": upload_id,
            "chunk_index": index,
            "base64_data": base64.b64encode(piece).decode("ascii"),
        })
    done = await _exchange(ws, "aibot_upload_media_finish", {"upload_id": upload_id})
    media_id = (done.get("body") or {}).get("media_id")
    if not media_id:
        raise RuntimeError("upload rejected")
    return media_id


async def _exchange(ws, cmd, body, timeout=30):
    from aibot.utils import generate_req_id

    manager = ws._ws_manager
    req_id = generate_req_id("media")
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    original = manager._handle_frame

    def wrapped(frame):
        headers = frame.get("headers") or {}
        if headers.get("req_id") == req_id:
            if not future.done():
                future.set_result(frame)
            return
        original(frame)

    manager._handle_frame = wrapped
    try:
        await manager.send({"cmd": cmd, "headers": {"req_id": req_id}, "body": body})
        frame = await asyncio.wait_for(future, timeout)
    finally:
        if manager._handle_frame is wrapped:
            manager._handle_frame = original
    if frame.get("errcode") not in (None, 0):
        raise RuntimeError("upload rejected")
    return frame
