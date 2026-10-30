"""Write the whole dataset as one Parquet file plus a Hugging Face dataset card.

python -m diem_chuan.export --out dist/hf
"""

from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
from string import Template

import pandas as pd

from diem_chuan.load import DATA_DIR, load_methods, load_scores, load_sources, load_universities

PARQUET = "diem_chuan.parquet"
HF_REPO = "HongTin2104/diem-chuan-vn"

COLUMNS = [
    "university",
    "university_name",
    "university_short_name",
    "city",
    "year",
    "major_code",
    "major_name",
    "method",
    "method_name_vi",
    "method_name_en",
    "subject_groups",
    "score",
    "scale",
    "note",
    "source",
    "source_page_url",
    "source_file_url",
    "source_accessed",
]


def build_table(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """One row per score, with the university, method and source details joined in."""
    universities = load_universities(data_dir).rename(
        columns={
            "code": "university",
            "name": "university_name",
            "short_name": "university_short_name",
        }
    )
    methods = load_methods(data_dir).rename(
        columns={"name_vi": "method_name_vi", "name_en": "method_name_en"}
    )
    sources = load_sources(data_dir).rename(
        columns={
            "id": "source",
            "page_url": "source_page_url",
            "file_url": "source_file_url",
            "accessed": "source_accessed",
        }
    )
    df = load_scores(data_dir)
    for key, details in [
        (
            "university",
            universities[["university", "university_name", "university_short_name", "city"]],
        ),
        ("method", methods[["method", "method_name_vi", "method_name_en"]]),
        ("source", sources[["source", "source_page_url", "source_file_url", "source_accessed"]]),
    ]:
        df = df.merge(details, on=key, how="left", validate="many_to_one")
        # Empty cells are read as "", so NaN here can only mean the key was not found.
        missing = sorted(set(df.loc[df[details.columns[1]].isna(), key]))
        if missing:
            raise ValueError(f"{key} not found: {', '.join(missing)}")
    return df[COLUMNS]


def size_category(rows: int) -> str:
    """The `size_categories` value Hugging Face expects in the card."""
    for limit, label in [(1_000, "n<1K"), (10_000, "1K<n<10K"), (100_000, "10K<n<100K")]:
        if rows < limit:
            return label
    return "100K<n<1M"


def card(df: pd.DataFrame, hf_repo: str = HF_REPO) -> str:
    template = Template(files("diem_chuan").joinpath("dataset_card.md").read_text(encoding="utf-8"))
    return template.substitute(
        hf_repo=hf_repo,
        parquet=PARQUET,
        version=version("diem-chuan-vn"),
        rows=f"{len(df):,}",
        size_category=size_category(len(df)),
        universities=df["university"].nunique(),
        sources=df["source"].nunique(),
        first_year=df["year"].min(),
        last_year=df["year"].max(),
    )


def export(out_dir: Path, data_dir: Path = DATA_DIR, hf_repo: str = HF_REPO) -> pd.DataFrame:
    df = build_table(data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / PARQUET, index=False)
    (out_dir / "README.md").write_text(card(df, hf_repo), encoding="utf-8", newline="\n")
    return df


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m diem_chuan.export",
        description="Write the dataset as one Parquet file plus a Hugging Face dataset card.",
    )
    parser.add_argument("--out", type=Path, default=Path("dist/hf"))
    parser.add_argument("--hf-repo", default=HF_REPO, help="used in the card's loading examples")
    args = parser.parse_args(argv)

    df = export(args.out, hf_repo=args.hf_repo)
    print(f"Wrote {len(df)} rows to {args.out / PARQUET} and the card to {args.out / 'README.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
