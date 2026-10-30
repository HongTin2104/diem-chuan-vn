"""Polite fetching of official announcement pages, and HTML table extraction.

Pages are cached under data/raw/ (not committed), so re-running an extractor does not
hit the university's site again.
"""

import hashlib
import html
import re
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

from diem_chuan.load import DATA_DIR

USER_AGENT = "diem-chuan-vn/0.1 (+https://github.com/HongTin2104/diem-chuan-vn)"
DELAY_SECONDS = 2.0
CACHE_DIR = DATA_DIR / "raw"

_last_request = 0.0
_robots: dict[str, urllib.robotparser.RobotFileParser] = {}


class Disallowed(Exception):
    """robots.txt does not allow this URL."""


def _allowed(url: str) -> bool:
    parts = urllib.parse.urlsplit(url)
    root = f"{parts.scheme}://{parts.netloc}"
    if root not in _robots:
        parser = urllib.robotparser.RobotFileParser(root + "/robots.txt")
        try:
            parser.read()
        except OSError:
            # No reachable robots.txt means no stated restrictions.
            parser.parse([])
        _robots[root] = parser
    return _robots[root].can_fetch(USER_AGENT, url)


def fetch(url: str, cache_dir: Path = CACHE_DIR) -> bytes:
    """Return the body of `url`, from the cache when possible."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / hashlib.sha256(url.encode()).hexdigest()[:16]
    if cached.exists():
        return cached.read_bytes()
    if not _allowed(url):
        raise Disallowed(url)

    global _last_request
    wait = DELAY_SECONDS - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
    _last_request = time.monotonic()
    cached.write_bytes(body)
    return body


def _cell_text(cell: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", cell))
    return re.sub(r"\s+", " ", text).strip()


def html_tables(page: str) -> list[list[list[str]]]:
    """Every <table> in `page` as a list of rows of cell texts. Nested tables are not handled."""
    tables = []
    for table in re.findall(r"<table.*?</table>", page, flags=re.S | re.I):
        rows = []
        for row in re.findall(r"<tr.*?</tr>", table, flags=re.S | re.I):
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S | re.I)
            rows.append([_cell_text(c) for c in cells])
        tables.append(rows)
    return tables


def parse_score(text: str) -> str:
    """'24,60' or '24.60' -> '24.60'; keeps the digits as published."""
    value = text.strip().replace(",", ".")
    float(value)  # raises on anything that is not a number
    return value


def parse_groups(text: str) -> str:
    """'A00; B00, D07' -> 'A00 B00 D07'."""
    return " ".join(g for g in re.split(r"[\s,;]+", text.strip()) if g)
