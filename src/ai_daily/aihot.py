import re

_TAIL = re.compile(r"(?:（[^）]*）|\([^)]*\))\s*$")

def clean_source(name: str) -> str:
    cleaned = name.strip()
    while True:
        nxt = _TAIL.sub("", cleaned).strip()
        if nxt == cleaned:
            return cleaned
        cleaned = nxt
