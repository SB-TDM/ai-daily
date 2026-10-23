"""Local newspaper generation and the WeCom long-connection receiver."""
import argparse
import json
from pathlib import Path
import sys

from .generate import generate_poster
from .receiver import serve_long


def _sdk_client(options):
    import asyncio
    import secrets

    from aibot import WSClient, WSClientOptions

    ws = WSClient(WSClientOptions(
        bot_id=options["bot_id"],
        secret=options["secret"],
        max_reconnect_attempts=options["max_reconnect_attempts"],
    ))

    class Adapter:
        def __init__(self):
            self.loop = None

        def on(self, event, handler):
            async def wrapped(frame):
                self.loop = asyncio.get_running_loop()
                handler(frame)

            ws.on(event, wrapped)

        def connect(self):
            ws.run()

        def _run(self, coro):
            if self.loop and self.loop.is_running():
                try:
                    asyncio.get_running_loop()
                    return asyncio.ensure_future(coro)
                except RuntimeError:
                    return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout=60)
            return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout=60)

        def reply_text(self, frame, text):
            self._run(ws.reply_stream(frame, secrets.token_hex(8), text, True))

        def preview_image(self, frame, png):
            self._run(_preview(ws, frame, png))

    return Adapter()


async def _preview(ws, frame, png):
    from .link import send_chat_image

    await send_chat_image(ws, frame, png)


def _serve(root, host, port):
    return serve_long(root, _sdk_client)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ai_daily")
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--force", action="store_true")
    generate.add_argument("--root", default=".")
    generate.add_argument("--report")
    generate.add_argument("--offline", action="store_true")
    serve = sub.add_parser("serve")
    serve.add_argument("--root", default=".")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8787)
    args = parser.parse_args(argv)
    if args.command == "serve":
        return _serve(args.root, args.host, args.port)
    if args.report and not args.offline:
        parser.error("--report requires --offline")
    report = json.loads(Path(args.report).read_text(encoding="utf-8")) if args.report else None
    result = generate_poster(args.root, force=args.force, report=report, offline=args.offline)
    print(result.status)
    if result.path:
        print(result.path)
    return 0 if result.status in ("ready", "already_ready") else 1


if __name__ == "__main__":
    sys.exit(main())
