from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app" / "app.py")


def run(**numbers) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    for i, value in numbers.items():
        at.number_input[int(i.removeprefix("n"))].set_value(value).run()
    return at


def test_app_starts_with_suggestions():
    at = run()
    assert not at.exception
    table = at.dataframe[0].value
    assert len(table) > 0
    assert set(table["Mức"]) <= {"thử thách", "vừa sức", "an toàn"}
    assert (table["Điểm chuẩn"] <= 26).all()  # default score 25, reach is 1 point


def test_low_score_shows_a_message():
    at = run(n0=5.0)
    assert not at.exception
    assert "Chưa có ngành nào" in at.info[0].value


def test_lookup_shows_history_and_sources():
    at = run()
    at.selectbox(key="lookup_uni").set_value("BKA").run()
    assert not at.exception
    headers = [s.value for s in at.subheader]
    assert any("thang 30" in h for h in headers)
    assert any("thông báo chính thức" in m.value for m in at.markdown)
