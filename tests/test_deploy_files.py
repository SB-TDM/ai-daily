from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_compose_binds_localhost_only():
    text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "127.0.0.1:8787:8787" in text
    assert "0.0.0.0:8787" not in text
    assert "AI_DAILY_FONT_DIR" in text
    assert "/fonts" in text
    assert "/app/runtime" in text


def test_image_does_not_copy_secrets():
    docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    ignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert "COPY . ." not in docker
    assert ".env" in ignore
    assert "data" in ignore
