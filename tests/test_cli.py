import json
from datetime import date

from ai_daily.__main__ import main


def test_offline_report_generates_without_network(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("ai_daily.generate.beijing_date", lambda now=None: date(2026, 10, 22))
    report = {
        "date": "2026-10-22",
        "lead": {"title": "Lead", "leadParagraph": "Paragraph."},
        "sections": [],
        "flashes": [],
    }
    path = tmp_path / "report.json"
    path.write_text(json.dumps({"report": report}), encoding="utf-8")

    code = main(["generate", "--root", str(tmp_path), "--report", str(path), "--offline"])

    assert code == 0
    output = capsys.readouterr().out
    assert output.splitlines()[0] == "ready"
    assert (tmp_path / "data" / "posters" / "2026-10-22.png").exists()


def test_report_without_offline_is_refused():
    try:
        main(["generate", "--report", "report.json"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("A supplied report must not be mixed with network fetching")
