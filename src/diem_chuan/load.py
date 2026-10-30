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


def load_programme_aliases(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Old programme codes and the current code of the same programme. The file is optional."""
    path = data_dir / "programme_aliases.csv"
    if not path.exists():
        return pd.DataFrame(columns=["university", "code", "same_as"], dtype=str)
    return pd.read_csv(path, **_READ)


def load_scores(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """All score rows, one file per university.

    Adds `university`, and `programme`: the programme's current code, so that the years before
    and after a code change can be joined. `major_code` stays as published.
    """
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
    aliases = load_programme_aliases(data_dir)
    keys = zip(aliases["university"], aliases["code"], strict=True)
    current = dict(zip(keys, aliases["same_as"], strict=True))
    df["programme"] = [
        current.get((u, c), c) for u, c in zip(df["university"], df["major_code"], strict=True)
    ]
    return df
