import csv

import pytest

from diem_chuan.sources import bka, extractor, replace_rows
from diem_chuan.sources.__main__ import main


def read(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_extractor_lookup():
    assert extractor("bka-2023") is bka.rows_2023
    with pytest.raises(KeyError, match="no extractor for bka-1999"):
        extractor("bka-1999")


def test_replace_rows_keeps_other_sources_and_orders(tmp_path):
    (tmp_path / "scores").mkdir()
    replace_rows(
        "BKA", "bka-2024", [{"year": "2024", "method": "thpt", "major_code": "IT1"}], tmp_path
    )
    replace_rows(
        "BKA", "bka-2023", [{"year": "2023", "method": "tsa", "major_code": "IT1"}], tmp_path
    )
    replace_rows(
        "BKA", "bka-2023", [{"year": "2023", "method": "thpt", "major_code": "IT2"}], tmp_path
    )

    rows = read(tmp_path / "scores" / "BKA.csv")
    assert [(r["year"], r["method"], r["major_code"], r["source"]) for r in rows] == [
        ("2023", "thpt", "IT2", "bka-2023"),
        ("2024", "thpt", "IT1", "bka-2024"),
    ]
    assert rows[0]["note"] == ""


def test_bka_table_rows():
    table = [
        bka.HEADER,
        ["1", "IT1", "Khoa học Máy tính", "A00; A01", "29,42"],
        ["2", "IT2", "Kỹ thuật Máy tính", "K00", "75.0"],
    ]
    rows = bka._table_rows(table, "thpt", "30")
    assert rows[0]["subject_groups"] == "A00 A01"
    assert rows[0]["score"] == "29.42"
    assert rows[1]["subject_groups"] == ""


def test_bka_table_rows_rejects_changed_layout():
    with pytest.raises(ValueError, match="unexpected header"):
        bka._table_rows([["Mã", "Điểm"]], "thpt", "30")
    with pytest.raises(ValueError, match="unexpected row"):
        bka._table_rows([bka.HEADER, ["Ghi chú", "", "", "", ""]], "thpt", "30")


def test_main_writes_rows(tmp_path, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(
        "diem_chuan.sources.__main__.extractor", lambda sid: lambda: [{"year": "2023"}]
    )
    monkeypatch.setattr(
        "diem_chuan.sources.__main__.replace_rows",
        lambda uni, sid, rows: calls.append((uni, sid)) or len(rows),
    )
    assert main(["bka-2023"]) == 0
    assert calls == [("BKA", "bka-2023")]
    assert "1 rows written to data/scores/BKA.csv" in capsys.readouterr().out
