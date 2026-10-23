from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    reply: str
    start_tool: bool
    send: bool
    schedule: str | None = None
    secret: str | None = None
    image_patch: dict | None = None


HELP = """菲比啾比！这些话我听得懂：
生成日报 — 做今天的日报，图发回这次聊天
重新生成 — 重做今天的图
发送 — 把今天的图发到群里
时间 08:30 — 改提醒时间，例如 时间 09:00
参数 — 看看现在的生图参数
帮助 — 再看一遍"""
START = "好，我去做今天的日报啦"
BUSY = "还在做呢，等我一下"
ALREADY = "今天已经做好啦。要发到群里说发送，想重做说重新生成"
SENT = "发到群里啦"
MISSING = "今天还没有图呢。先说生成日报"
CHANGED = "改好啦"


def _unknown(text):
    return f"「{text}」我没听懂。发送「帮助」，我再告诉你。"


def _clock(text):
    clock = text.removeprefix("时间 ")
    hour, _, minute = clock.partition(":")
    if not hour.isdigit() or not minute.isdigit() or len(hour) != 2 or len(minute) != 2:
        return None
    if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
        return None
    return clock


def handle_command(text, *, generating, poster_ready, image=None, secret=None):
    if text == "参数":
        current = image or {}
        model = current.get("model") or ""
        base_url = current.get("base_url") or ""
        return Decision(
            reply=f"{model} {base_url}".strip(),
            start_tool=False,
            send=False,
        )
    if text.startswith("参数 其他 "):
        rest = text.removeprefix("参数 其他 ")
        key, _, value = rest.partition(" ")
        if not key or not value:
            return Decision(reply=_unknown(text), start_tool=False, send=False)
        return Decision(
            reply=CHANGED,
            start_tool=False,
            send=False,
            image_patch={key: value},
        )
    if text.startswith("参数 地址 "):
        base_url = text.removeprefix("参数 地址 ")
        return Decision(
            reply=f"地址改好啦：{base_url}",
            start_tool=False,
            send=False,
            image_patch={"base_url": base_url},
        )
    if text.startswith("参数 模型 "):
        model = text.removeprefix("参数 模型 ")
        return Decision(
            reply=f"模型改好啦：{model}",
            start_tool=False,
            send=False,
            image_patch={"model": model},
        )
    if text.startswith("参数 密钥 "):
        return Decision(
            reply=CHANGED,
            start_tool=False,
            send=False,
            secret=text.removeprefix("参数 密钥 "),
        )
    if text.startswith("时间"):
        clock = _clock(text) if text.startswith("时间 ") else None
        if clock is None:
            return Decision(reply=_unknown(text), start_tool=False, send=False)
        return Decision(
            reply=f"好，提醒时间改成 {clock} 啦",
            start_tool=False,
            send=False,
            schedule=clock,
        )
    if text in ("帮助", "help", "menu", "菜单"):
        return Decision(reply=HELP, start_tool=False, send=False)
    if generating and text in ("生成日报", "重新生成", "发送"):
        return Decision(reply=BUSY, start_tool=False, send=False)
    if text == "发送":
        if poster_ready:
            return Decision(reply=SENT, start_tool=False, send=True)
        return Decision(reply=MISSING, start_tool=False, send=False)
    if text == "重新生成":
        return Decision(reply=START, start_tool=True, send=False)
    if text == "生成日报":
        if poster_ready:
            return Decision(reply=ALREADY, start_tool=False, send=False)
        return Decision(reply=START, start_tool=True, send=False)
    return Decision(reply=_unknown(text), start_tool=False, send=False)
