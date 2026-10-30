from pdfgen import write_pdf

from citefield.cli import main

CONFIG = """
fields:
  - name: engine_manufacturer
    description: Engine manufacturer.
settings:
  llm:
    model: openrouter/google/gemini-3.1-flash-lite
"""


def test_validate_config(tmp_path, capsys):
    good = tmp_path / "good.yaml"
    good.write_text(CONFIG, encoding="utf-8")
    assert main(["validate-config", str(good)]) == 0
    assert "OK, 1 fields" in capsys.readouterr().out

    bad = tmp_path / "bad.yaml"
    bad.write_text("fields:\n  - name: Bad Name\n    description: x\n", encoding="utf-8")
    assert main(["validate-config", str(bad)]) == 1
    assert "snake_case" in capsys.readouterr().err

    assert main(["validate-config", str(tmp_path / "missing.yaml")]) == 1


def test_inspect(tmp_path, capsys):
    pdf = write_pdf(tmp_path / "m.pdf", ["Engine manufacturer: Onan"])
    assert main(["inspect", str(pdf)]) == 0
    out = capsys.readouterr().out
    assert "[[page 1 · low text]]\nEngine manufacturer: Onan" in out
    assert "1 units, parser pdfplumber" in out


def test_extract_dry_run_makes_no_calls(tmp_path, capsys):
    config = tmp_path / "fields.yaml"
    config.write_text(CONFIG, encoding="utf-8")
    pdf = write_pdf(tmp_path / "m.pdf", ["Engine manufacturer: Onan"])
    out = tmp_path / "out"
    assert main(["extract", str(pdf), "-c", str(config), "-o", str(out), "--dry-run"]) == 0
    assert "1 chunk(s) × 1 field batch(es) × 1 run(s) = 1 call(s)" in capsys.readouterr().out
    assert not out.exists()


def test_extract_dir_reports_broken_files_and_goes_on(tmp_path, capsys):
    config = tmp_path / "fields.yaml"
    config.write_text(CONFIG, encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    write_pdf(docs / "good.pdf", ["Engine manufacturer: Onan"])
    (docs / "broken.pdf").write_text("<html>error 523</html>", encoding="utf-8")
    out = tmp_path / "out"
    assert main(["extract", str(docs), "-c", str(config), "-o", str(out), "--dry-run"]) == 1
    captured = capsys.readouterr()
    assert "broken.pdf: can't parse" in captured.err
    assert "good.pdf: 1 chunk(s)" in captured.out
