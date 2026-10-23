import re


def _server_blocks(dump):
    blocks, i = [], 0
    while True:
        start = dump.find("server", i)
        if start < 0:
            return blocks
        brace = dump.find("{", start)
        if brace < 0:
            return blocks
        depth, j = 0, brace
        while j < len(dump):
            depth += dump[j] == "{"
            depth -= dump[j] == "}"
            if depth == 0:
                blocks.append(dump[brace + 1:j])
                i = j + 1
                break
            j += 1
        else:
            return blocks


def certificate_from_dump(dump):
    for block in _server_blocks(dump):
        names = re.findall(r"server_name\s+([^;]+);", block)
        tokens = names[0].split() if names else []
        if "string.ink" not in tokens or "daily.string.ink" in tokens:
            continue
        cert = re.search(r"ssl_certificate\s+([^;]+);", block)
        key = re.search(r"ssl_certificate_key\s+([^;]+);", block)
        if cert and key and not cert.group(1).strip().startswith("ssl_certificate_key"):
            return cert.group(1).strip(), key.group(1).strip()
    raise ValueError("缺少证书路径")


def nginx_site(certificate, certificate_key):
    if not certificate or not certificate_key or "\n" in certificate or "\n" in certificate_key:
        raise ValueError("证书路径无效")
    return (
        "server {\n"
        "    listen 80;\n"
        "    server_name daily.string.ink;\n"
        "    return 301 https://$host$request_uri;\n"
        "}\n"
        "server {\n"
        "    listen 443 ssl;\n"
        "    server_name daily.string.ink;\n"
        f"    ssl_certificate {certificate};\n"
        f"    ssl_certificate_key {certificate_key};\n"
        "    location /wecom {\n"
        "        proxy_pass http://127.0.0.1:8787;\n"
        "        proxy_set_header Host $host;\n"
        "    }\n"
        "}\n"
    )
