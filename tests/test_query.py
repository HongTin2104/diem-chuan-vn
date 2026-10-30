import pandas as pd
import pytest

from diem_chuan import load_scores
from diem_chuan.query import history, suggest


def frame(rows):
    cols = ["university", "year", "major_code", "major_name", "method", "score", "scale"]
    df = pd.DataFrame(rows, columns=cols)
    df["subject_groups"] = ""
    df["note"] = ""
    return df


DF = frame(
    [
        ("AAA", 2024, "IT", "CNTT", "thpt", 26.0, 30),
        ("AAA", 2025, "IT", "CNTT", "thpt", 27.0, 30),
        ("AAA", 2025, "EC", "Kinh tế", "thpt", 24.0, 30),
        ("AAA", 2024, "OLD", "Ngành đã đóng", "thpt", 20.0, 30),
        ("AAA", 2025, "IT", "CNTT", "tsa", 80.0, 100),
        ("BBB", 2025, "CS", "KHMT", "thpt", 28.5, 30),
        ("BBB", 2025, "CS", "KHMT", "thpt", 28.0, 30),  # a second subject group
    ]
)


def test_suggest_levels_and_order():
    got = suggest(DF, 27.5)
    assert [(s.university, s.major_code, s.level, s.gap) for s in got] == [
        ("BBB", "CS", "thử thách", -0.5),
        ("AAA", "IT", "vừa sức", 0.5),
        ("AAA", "EC", "an toàn", 3.5),
    ]


def test_suggest_uses_lowest_group_and_skips_closed_programmes():
    got = {s.major_code: s for s in suggest(DF, 30)}
    assert got["CS"].cutoff == 28.0
    assert "OLD" not in got


def test_suggest_never_mixes_scales():
    got = suggest(DF, 81, method="tsa", scale=100)
    assert [s.major_code for s in got] == ["IT"]
    assert suggest(DF, 81, method="thpt", scale=100) == []


def test_suggest_filters_universities_and_drops_out_of_reach():
    assert [s.major_code for s in suggest(DF, 27.5, universities=["AAA"])] == ["IT", "EC"]
    assert suggest(DF, 20) == []


def test_reason_mentions_gap_and_trend():
    it = next(s for s in suggest(DF, 27.5) if s.major_code == "IT")
    assert it.trend == pytest.approx(1.0)
    assert it.reason() == (
        "Điểm của bạn cao hơn điểm chuẩn 2025 (27) 0.50 điểm; "
        "điểm chuẩn tăng trung bình 1.00 điểm/năm (2 năm có dữ liệu)."
    )
    cs = next(s for s in suggest(DF, 27.5) if s.major_code == "CS")
    assert cs.reason().startswith("Điểm của bạn thấp hơn điểm chuẩn 2025 (28) 0.50 điểm")
    assert "chưa thấy xu hướng" in cs.reason()


def test_history_is_sorted():
    h = history(DF, "AAA", "IT", "thpt")
    assert list(h["year"]) == [2024, 2025]
    assert list(h["score"]) == [26.0, 27.0]


def test_suggest_on_real_data():
    got = suggest(load_scores(), 27.0)
    assert got, "the committed data should give suggestions for a 27"
    assert all(s.cutoff <= 28.0 for s in got)
    assert {s.university for s in got} >= {"BKA", "KHA"}


def test_cli_prints_suggestions(capsys):
    from diem_chuan.query import main

    assert main(["27", "--university", "BKA", "--limit", "2"]) == 0
    out = capsys.readouterr().out
    assert out.count("[") == 2
    assert "BKA" in out
    assert out.rstrip().endswith("programme(s) in reach.")
