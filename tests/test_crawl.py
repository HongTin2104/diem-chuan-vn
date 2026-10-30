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


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self.body


def test_fetch_downloads_waits_and_caches(tmp_path, monkeypatch):
    requests, sleeps = [], []
    monkeypatch.setattr(crawl, "_allowed", lambda url: True)
    monkeypatch.setattr(crawl.time, "sleep", sleeps.append)
    monkeypatch.setattr(crawl, "_last_request", crawl.time.monotonic())

    def urlopen(request, timeout):
        requests.append(request)
        return FakeResponse(b"<table></table>")

    monkeypatch.setattr(crawl.urllib.request, "urlopen", urlopen)
    url = "https://example.edu.vn/diem-chuan-2025"
    assert crawl.fetch(url, cache_dir=tmp_path) == b"<table></table>"
    assert crawl.fetch(url, cache_dir=tmp_path) == b"<table></table>"

    assert len(requests) == 1  # the second call is served from the cache
    assert requests[0].get_header("User-agent") == crawl.USER_AGENT
    assert len(sleeps) == 1 and 0 < sleeps[0] <= crawl.DELAY_SECONDS


def test_fetch_encodes_vietnamese_urls(tmp_path, monkeypatch):
    # FTU links to pages like /tuyensinh/ftu-thông-tin-tuyển-sinh-chung/...
    requests, checked = [], []
    monkeypatch.setattr(crawl, "_allowed", lambda url: checked.append(url) or True)
    monkeypatch.setattr(crawl.time, "sleep", lambda s: None)
    monkeypatch.setattr(
        crawl.urllib.request,
        "urlopen",
        lambda r, timeout: requests.append(r) or FakeResponse(b"ok"),
    )
    url = "https://ftu.edu.vn/tuyensinh/thông-tin?q=điểm chuẩn&page=2"
    assert crawl.fetch(url, cache_dir=tmp_path) == b"ok"
    encoded = (
        "https://ftu.edu.vn/tuyensinh/th%C3%B4ng-tin?q=%C4%91i%E1%BB%83m%20chu%E1%BA%A9n&page=2"
    )
    assert requests[0].full_url == encoded
    assert checked == [encoded]
    # The same page written either way is one cache entry.
    monkeypatch.setattr(crawl.urllib.request, "urlopen", None)
    assert crawl.fetch(encoded, cache_dir=tmp_path) == b"ok"


@pytest.mark.parametrize(
    "url",
    [
        "https://example.edu.vn/diem-chuan-2025",
        "https://example.edu.vn/a%20b/c?x=1&y=%C4%91",
        "https://example.edu.vn/sinh-vi%C3%AAn/66-hoc-bong",
    ],
)
def test_encoding_leaves_ascii_urls_alone(url):
    assert crawl.encode_url(url) == url


class FakeRobots:
    def __init__(self, url, lines=None, fail=False):
        self.url, self.lines, self.fail = url, lines, fail

    def read(self):
        if self.fail:
            raise OSError("unreachable")
        self.parse(self.lines)

    def parse(self, lines):
        self.disallowed = [line.split(": ")[1] for line in lines if line.startswith("Disallow")]

    def can_fetch(self, agent, url):
        return not any(crawl.urllib.parse.urlsplit(url).path.startswith(p) for p in self.disallowed)


@pytest.mark.parametrize(
    ("robots", "url", "allowed"),
    [
        ({"lines": ["User-agent: *", "Disallow: /admin"]}, "https://a.edu.vn/admin/x", False),
        ({"lines": ["User-agent: *", "Disallow: /admin"]}, "https://a.edu.vn/tin-tuc", True),
        ({"fail": True}, "https://a.edu.vn/admin/x", True),
    ],
)
def test_allowed_reads_robots_once(monkeypatch, robots, url, allowed):
    made = []

    def parser(robots_url):
        made.append(robots_url)
        return FakeRobots(robots_url, **robots)

    monkeypatch.setattr(crawl, "_robots", {})
    monkeypatch.setattr(crawl.urllib.robotparser, "RobotFileParser", parser)
    assert crawl._allowed(url) is allowed
    assert crawl._allowed(url) is allowed
    assert made == ["https://a.edu.vn/robots.txt"]


def test_encoding_converts_an_international_domain():
    assert crawl.encode_url("https://tênmiền.vn/a") == "https://xn--tnmin-hsa0954c.vn/a"
