"""Extractors for announcements that can be read by a program (HTML tables, PDFs).

One module per university, named after its code in lower case (`bka.py`). Each module
exposes `EXTRACTORS`, a mapping from a source id in data/sources.csv to a function that
returns that source's score rows. Run one with:

    python -m diem_chuan.sources bka-2023

Image-only announcements are typed into data/scores/ by hand instead.
"""

import csv
import importlib
from collections.abc import Callable, Iterable
from pathlib import Path

from diem_chuan.load import DATA_DIR
from diem_chuan.schema import SCORE_COLUMNS

Row = dict[str, str]
Extractor = Callable[[], list[Row]]


def extractor(source_id: str) -> Extractor:
    university = source_id.split("-", 1)[0]
    module = importlib.import_module(f"diem_chuan.sources.{university}")
    try:
        return module.EXTRACTORS[source_id]
    except KeyError:
        raise KeyError(f"{module.__name__} has no extractor for {source_id}") from None


def replace_rows(
    university: str, source_id: str, rows: Iterable[Row], data_dir: Path = DATA_DIR
) -> int:
    """Replace the rows of `source_id` in scores/<UNIVERSITY>.csv with `rows`.

    Rows from other sources are kept. The file stays ordered by year, then method, with
    rows of one source in the order the source lists them.
    """
    path = data_dir / "scores" / f"{university}.csv"
    kept: list[Row] = []
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f:
            kept = [r for r in csv.DictReader(f) if r["source"] != source_id]
    new = [{col: row.get(col, "") for col in SCORE_COLUMNS} for row in rows]
    for row in new:
        row["source"] = source_id
    merged = sorted(kept + new, key=lambda r: (r["year"], r["method"]))
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SCORE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(merged)
    return len(new)
