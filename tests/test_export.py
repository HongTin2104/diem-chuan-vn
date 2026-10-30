import shutil

import pandas as pd
import pytest

from diem_chuan.export import COLUMNS, PARQUET, build_table, card, export, main, size_category
from diem_chuan.load import DATA_DIR, load_scores


@pytest.fixture
def data_copy(tmp_path):
    return shutil.copytree(DATA_DIR, tmp_path / "data", ignore=shutil.ignore_patterns("raw"))


def test_table_keeps_every_score_row_and_finds_every_detail():
    df = build_table()
    scores = load_scores()
    assert list(df.columns) == COLUMNS
    assert len(df) == len(scores)
    pd.testing.assert_series_equal(df["score"], scores["score"])
    assert df[COLUMNS].notna().all().all()
    assert (df["source_page_url"] != "").all()


def test_joins_the_right_details():
    row = build_table().query("source == 'bka-2025'").iloc[0]
    assert row["university_short_name"] == "HUST"
    assert row["source_page_url"].startswith("https://")


@pytest.mark.parametrize(
    ("file", "old", "new", "message"),
    [
        ("scores/BKA.csv", ",bka-2025,", ",bka-1999,", "source not found: bka-1999"),
        ("universities.csv", "BKA,", "XXX,", "university not found: BKA"),
        ("methods.csv", "\nthpt,", "\nexam,", "method not found: thpt"),
    ],
)
def test_unknown_key_is_reported(data_copy, file, old, new, message):
    path = data_copy / file
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        build_table(data_copy)


@pytest.mark.parametrize(
    ("rows", "label"),
    [(999, "n<1K"), (1_000, "1K<n<10K"), (10_000, "10K<n<100K"), (100_000, "100K<n<1M")],
)
def test_size_category(rows, label):
    assert size_category(rows) == label


def test_card_is_filled_from_the_data():
    df = build_table()
    text = card(df, hf_repo="someone/scores")
    assert text.startswith("---\nlicense: cc-by-4.0\n")
    assert "- 1K<n<10K\n" in text
    assert f"{len(df):,} rows" in text
    assert f"{df['year'].min()}-{df['year'].max()}" in text
    assert 'load_dataset("someone/scores"' in text
    assert "$" not in text


def test_export_round_trips(tmp_path):
    df = export(tmp_path / "hf")
    pd.testing.assert_frame_equal(pd.read_parquet(tmp_path / "hf" / PARQUET), df)
    assert (tmp_path / "hf" / "README.md").read_bytes().count(b"\r") == 0


def test_main(tmp_path, capsys):
    assert main(["--out", str(tmp_path)]) == 0
    assert (tmp_path / PARQUET).exists()
    assert "rows to" in capsys.readouterr().out
