import hashlib

import pytest

from diem_chuan import crawl


def test_html_tables_reads_cells():
    page = """
    <p>x</p>
    <table><tr><th>Mã</th><th>Điểm&nbsp;chuẩn</th></tr>
    <tr><td><b>IT1</b></td><td>
      29,19 </td></tr></table>
    <TABLE><TR><TD>a</TD></TR></TABLE>
    """
    assert crawl.html_tables(page) == [[["Mã", "Điểm chuẩn"], ["IT1", "29,19"]], [["a"]]]


@pytest.mark.parametrize(("text", "value"), [("24,60", "24.60"), (" 27.3 ", "27.3"), ("28", "28")])
def test_parse_score(text, value):
    assert crawl.parse_score(text) == value


def test_parse_score_rejects_text():
    with pytest.raises(ValueError):
        crawl.parse_score("-")


def test_parse_groups():
    assert crawl.parse_groups("A00; B00, D07") == "A00 B00 D07"
    assert crawl.parse_groups(" ") == ""


def test_fetch_uses_cache_without_network(tmp_path, monkeypatch):
    url = "https://example.edu.vn/diem-chuan"
    name = hashlib.sha256(url.encode()).hexdigest()[:16]
    (tmp_path / name).write_bytes(b"cached")
    monkeypatch.setattr(crawl.urllib.request, "urlopen", None)  # any request would fail
    assert crawl.fetch(url, cache_dir=tmp_path) == b"cached"


def test_fetch_respects_robots(tmp_path, monkeypatch):
    monkeypatch.setattr(crawl, "_allowed", lambda url: False)
    with pytest.raises(crawl.Disallowed):
        crawl.fetch("https://example.edu.vn/private", cache_dir=tmp_path)
