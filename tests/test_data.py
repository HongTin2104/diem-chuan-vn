"""Checks on the committed dataset itself, not on fixtures."""

from diem_chuan import load_scores, load_sources
from diem_chuan.validate import validate


def test_committed_data_is_valid():
    assert validate() == []


def test_every_source_is_used():
    used = set(load_scores()["source"])
    assert set(load_sources()["id"]) - used == set()


def test_scores_stay_within_their_scale():
    df = load_scores()
    assert (df["score"] <= df["scale"]).all()
    assert set(df.loc[df["method"] == "thpt", "scale"]) == {30.0}


def test_empty_data_folder_loads_as_empty_frame(tmp_path):
    from diem_chuan.load import load_scores

    (tmp_path / "scores").mkdir()
    assert load_scores(tmp_path).empty
