"""Check every file under data/ and report problems as `file:line: message`.

Run with `python -m diem_chuan.validate` (or `diem-chuan-validate`). Exit code 1 means
at least one problem was found.
"""

import argparse
import csv
import datetime as dt
import io
import sys
import unicodedata
from pathlib import Path

import pandas as pd

from diem_chuan import schema
from diem_chuan.load import _READ, DATA_DIR, score_files


class Report:
    def __init__(self, root: Path):
        self.root = root
        self.errors: list[str] = []

    def add(self, path: Path, row: int | None, message: str) -> None:
        name = path.relative_to(self.root.parent).as_posix()
        # Row 0 of a frame is line 2 of the file, after the header.
        where = f"{name}:{row + 2}" if row is not None else name
        self.errors.append(f"{where}: {message}")


def _read(path: Path, columns: list[str], report: Report) -> pd.DataFrame | None:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        report.add(path, None, "file starts with a BOM; save as UTF-8 without BOM")
        return None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        report.add(path, None, "file is not valid UTF-8")
        return None
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or rows[0] != columns:
        report.add(path, None, f"columns must be exactly: {','.join(columns)}")
        return None
    # pandas would quietly shift a row with an extra comma, e.g. a score written 27,5.
    bad = [i for i, r in enumerate(rows[1:]) if len(r) != len(columns)]
    for i in bad:
        report.add(path, i, f"row has {len(rows[i + 1])} fields, expected {len(columns)}")
    if bad:
        return None
    df = pd.read_csv(path, **_READ)
    for i, row in df.iterrows():
        for col, value in row.items():
            if value != value.strip():
                report.add(path, i, f"{col} has leading or trailing spaces")
            # Composed and decomposed Vietnamese look the same but compare unequal.
            if unicodedata.normalize("NFC", value) != value:
                report.add(path, i, f"{col} is not in Unicode NFC form")
    return df


def _float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def _check_universities(data_dir: Path, report: Report) -> set[str]:
    path = data_dir / "universities.csv"
    df = _read(path, schema.UNIVERSITY_COLUMNS, report)
    if df is None:
        return set()
    for i, row in df.iterrows():
        if not schema.UNIVERSITY_CODE_RE.match(row["code"]):
            report.add(path, i, f"code {row['code']!r} is not three capital letters")
        if not row["name"]:
            report.add(path, i, "name is empty")
        if row["ownership"] not in schema.OWNERSHIPS:
            report.add(path, i, f"ownership must be one of {sorted(schema.OWNERSHIPS)}")
        if not row["website"].startswith("https://"):
            report.add(path, i, "website must start with https://")
    for code in df.loc[df["code"].duplicated(), "code"]:
        report.add(path, None, f"code {code} is listed more than once")
    return set(df["code"])


def _check_methods(data_dir: Path, report: Report) -> set[str]:
    path = data_dir / "methods.csv"
    df = _read(path, schema.METHOD_COLUMNS, report)
    if df is None:
        return set()
    for method in df.loc[df["method"].duplicated(), "method"]:
        report.add(path, None, f"method {method} is listed more than once")
    return set(df["method"])


def _check_sources(
    data_dir: Path, universities: set[str], report: Report
) -> dict[str, tuple[str, int, int]]:
    """Return {source id: (university, first year, last year)}."""
    path = data_dir / "sources.csv"
    df = _read(path, schema.SOURCE_COLUMNS, report)
    if df is None:
        return {}
    sources = {}
    for i, row in df.iterrows():
        if row["university"] not in universities:
            report.add(path, i, f"university {row['university']!r} is not in universities.csv")
        years = schema.YEARS_RE.match(row["years"])
        if not years:
            report.add(path, i, "years must look like 2024 or 2021-2025")
            continue
        first = int(years.group(1))
        last = int(years.group(2) or first)
        expected_id = f"{row['university'].lower()}-{row['years']}"
        if row["id"] != expected_id:
            report.add(path, i, f"id must be {expected_id!r}")
        if not row["page_url"].startswith(("https://", "http://")):
            report.add(path, i, "page_url must be a link to the official page")
        # Several images of one announcement are listed space-separated.
        if any(not u.startswith(("https://", "http://")) for u in row["file_url"].split()):
            report.add(path, i, "file_url must be empty or links separated by spaces")
        if row["format"] not in schema.SOURCE_FORMATS:
            report.add(path, i, f"format must be one of {sorted(schema.SOURCE_FORMATS)}")
        if not schema.DATE_RE.match(row["accessed"]):
            report.add(path, i, "accessed must be a date like 2026-10-30")
        if row["id"] in sources:
            report.add(path, i, f"id {row['id']} is used more than once")
        sources[row["id"]] = (row["university"], first, last)
    return sources


def _check_scores(
    path: Path,
    universities: set[str],
    methods: set[str],
    sources: dict[str, tuple[str, int, int]],
    report: Report,
) -> None:
    university = path.stem
    if university not in universities:
        report.add(path, None, f"file name {university!r} is not a code in universities.csv")
    df = _read(path, schema.SCORE_COLUMNS, report)
    if df is None:
        return
    if df.empty:
        report.add(path, None, "file has no rows")
        return

    this_year = dt.date.today().year
    for i, row in df.iterrows():
        year = int(row["year"]) if row["year"].isdigit() else None
        if year is None or not schema.FIRST_YEAR <= year <= this_year:
            report.add(path, i, f"year must be between {schema.FIRST_YEAR} and {this_year}")
        if not schema.MAJOR_CODE_RE.match(row["major_code"]):
            report.add(path, i, f"major_code {row['major_code']!r} has unexpected characters")
        if not row["major_name"]:
            report.add(path, i, "major_name is empty")
        if row["method"] not in methods:
            report.add(path, i, f"method {row['method']!r} is not in methods.csv")

        groups = row["subject_groups"].split()
        for group in groups:
            if not schema.SUBJECT_GROUP_RE.match(group):
                report.add(path, i, f"subject group {group!r} should look like A00 or D01")
        if len(groups) != len(set(groups)):
            report.add(path, i, "subject_groups repeats a group")

        score, scale = _float(row["score"]), _float(row["scale"])
        if scale is None or scale <= 0:
            report.add(path, i, "scale must be a positive number, e.g. 30")
        elif score is None:
            report.add(path, i, "score must be a number with a dot, e.g. 26.75")
        elif not 0 < score <= scale:
            report.add(path, i, f"score {score:g} is outside 0-{scale:g}")

        source = sources.get(row["source"])
        if source is None:
            report.add(path, i, f"source {row['source']!r} is not in sources.csv")
        else:
            owner, first, last = source
            if owner != university:
                report.add(path, i, f"source {row['source']} belongs to {owner}")
            if year is not None and not first <= year <= last:
                report.add(path, i, f"source {row['source']} only covers {first}-{last}")

    key = ["year", "major_code", "method", "subject_groups"]
    for i in df.index[df.duplicated(key, keep="first")]:
        report.add(path, i, "same year, major_code, method and subject_groups as an earlier row")


def validate(data_dir: Path = DATA_DIR) -> list[str]:
    report = Report(data_dir)
    universities = _check_universities(data_dir, report)
    methods = _check_methods(data_dir, report)
    sources = _check_sources(data_dir, universities, report)
    for path in score_files(data_dir):
        _check_scores(path, universities, methods, sources, report)
    return report.errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("data_dir", nargs="?", type=Path, default=DATA_DIR)
    args = parser.parse_args(argv)

    errors = validate(args.data_dir)
    for error in errors:
        print(error)
    n_files = len(score_files(args.data_dir))
    if errors:
        print(f"{len(errors)} problem(s) found", file=sys.stderr)
        return 1
    print(f"OK: {n_files} score file(s) checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
