import pytest

from ai_daily.site import certificate_from_dump, nginx_site

DUMP = """
server {
    server_name string.ink;
    ssl_certificate /etc/nginx/certs/string.ink.crt;
    ssl_certificate_key /etc/nginx/certs/string.ink.key;
}
"""


def test_certificate_comes_from_existing_site():
    assert certificate_from_dump(DUMP) == (
        "/etc/nginx/certs/string.ink.crt",
        "/etc/nginx/certs/string.ink.key",
    )


def test_new_site_does_not_replace_string_ink():
    text = nginx_site("/etc/nginx/certs/string.ink.crt", "/etc/nginx/certs/string.ink.key")
    assert "server_name daily.string.ink;" in text
    assert "server_name string.ink;" not in text
    assert "proxy_pass http://127.0.0.1:8787;" in text
    assert "location /wecom" in text


def test_daily_block_is_not_used_as_certificate_source():
    dump = DUMP + """
server {
    server_name daily.string.ink;
    ssl_certificate /tmp/daily.crt;
    ssl_certificate_key /tmp/daily.key;
}
"""
    assert certificate_from_dump(dump)[0] == "/etc/nginx/certs/string.ink.crt"


def test_missing_certificate_is_refused():
    with pytest.raises(ValueError):
        certificate_from_dump("server { server_name string.ink; }")


def test_nested_location_does_not_hide_certificate():
    dump = """
server {
    server_name string.ink;
    ssl_certificate /etc/nginx/certs/string.ink.crt;
    ssl_certificate_key /etc/nginx/certs/string.ink.key;
    location / {
        proxy_pass http://127.0.0.1:3000;
    }
}
"""
    assert certificate_from_dump(dump)[0] == "/etc/nginx/certs/string.ink.crt"
