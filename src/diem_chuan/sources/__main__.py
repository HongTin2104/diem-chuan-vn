import argparse
import sys

from diem_chuan.sources import extractor, replace_rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m diem_chuan.sources",
        description="Run an extractor and write its rows into data/scores/.",
    )
    parser.add_argument("source_ids", nargs="+", help="ids from data/sources.csv, e.g. bka-2023")
    args = parser.parse_args(argv)

    for source_id in args.source_ids:
        rows = extractor(source_id)()
        university = source_id.split("-", 1)[0].upper()
        n = replace_rows(university, source_id, rows)
        print(f"{source_id}: {n} rows written to data/scores/{university}.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
