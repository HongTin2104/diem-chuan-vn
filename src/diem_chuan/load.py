"""Read the dataset into pandas."""

import os
from pathlib import Path

import pandas as pd

# The data files live in the repository, next to src/. Set DIEM_CHUAN_DATA when the package
# is installed somewhere else.
DATA_DIR = Path(os.environ.get("DIEM_CHUAN_DATA", Path(__file__).resolve().parents[2] / "data"))

# Codes like 7480201 must stay strings, and an empty note is "", not NaN.
_READ = {"dtype": str, "keep_default_na": False, "encoding": "utf-8"}


def load_universities(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    return pd.read_csv(data_dir / "universities.csv", **_READ)


def load_sources(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    return pd.read_csv(data_dir / "sources.csv", **_READ)


def load_methods(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    return pd.read_csv(data_dir / "methods.csv", **_READ)


def load_subject_groups(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    return pd.read_csv(data_dir / "subject_groups.csv", **_READ)


def score_files(data_dir: Path = DATA_DIR) -> list[Path]:
    return sorted((data_dir / "scores").glob("*.csv"))


def load_scores(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """All score rows, one file per university, with a `university` column added."""
    frames = []
    for path in score_files(data_dir):
        df = pd.read_csv(path, **_READ)
        df.insert(0, "university", path.stem)
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["year"] = df["year"].astype(int)
    df["score"] = df["score"].astype(float)
    df["scale"] = df["scale"].astype(float)
    return df
