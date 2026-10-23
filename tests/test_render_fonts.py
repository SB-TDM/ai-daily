from ai_daily.render import font_path


def test_font_path_defaults_to_windows(monkeypatch):
    monkeypatch.delenv("AI_DAILY_FONT_DIR", raising=False)
    assert font_path("NotoSerifSC-VF.ttf") == r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"


def test_font_path_uses_directory(monkeypatch):
    monkeypatch.setenv("AI_DAILY_FONT_DIR", "/fonts")
    assert font_path("SourceHanSansCN-Regular.otf") == "/fonts/SourceHanSansCN-Regular.otf"
    assert font_path("SourceHanSansCN-Medium.otf") == "/fonts/SourceHanSansCN-Medium.otf"
