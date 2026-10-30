"""Look up cut-off history and suggest programmes for a given score.

Scores are only compared within one method and one scale: a 27 on the 30-point exam scale
says nothing about a 100-point combined score.
"""

from dataclasses import dataclass

import pandas as pd

# How far the student's score is above (+) or below (-) the latest cut-off.
SAFE_MARGIN = 1.0
REACH_MARGIN = -1.0


@dataclass(frozen=True)
class Suggestion:
    university: str
    major_code: str
    major_name: str
    cutoff: float
    year: int
    gap: float
    level: str
    trend: float | None
    years_seen: int

    def reason(self) -> str:
        """One sentence explaining the suggestion, in Vietnamese."""
        side = "cao hơn" if self.gap >= 0 else "thấp hơn"
        parts = [
            f"Điểm của bạn {side} điểm chuẩn {self.year} ({self.cutoff:g}) {abs(self.gap):.2f} điểm"
        ]
        if self.trend is not None:
            direction = "tăng" if self.trend > 0 else "giảm"
            if abs(self.trend) < 0.05:
                parts.append("điểm chuẩn gần như không đổi qua các năm")
            else:
                parts.append(
                    f"điểm chuẩn {direction} trung bình {abs(self.trend):.2f} điểm/năm "
                    f"({self.years_seen} năm có dữ liệu)"
                )
        else:
            parts.append("mới có dữ liệu 1 năm, chưa thấy xu hướng")
        return "; ".join(parts) + "."


def history(df: pd.DataFrame, university: str, major_code: str, method: str) -> pd.DataFrame:
    """Cut-offs of one programme over the years, oldest first."""
    rows = df[
        (df["university"] == university)
        & (df["major_code"] == major_code)
        & (df["method"] == method)
    ]
    return rows.sort_values("year")[["year", "score", "scale", "subject_groups", "note"]]


def _trend(scores: pd.Series, years: pd.Series) -> float | None:
    """Average change per year (least-squares slope), or None with fewer than two years."""
    if years.nunique() < 2:
        return None
    x = years - years.mean()
    return float((x * (scores - scores.mean())).sum() / (x**2).sum())


def _level(gap: float) -> str:
    if gap >= SAFE_MARGIN:
        return "an toàn"
    if gap >= 0:
        return "vừa sức"
    return "thử thách"


def suggest(
    df: pd.DataFrame,
    score: float,
    method: str = "thpt",
    scale: float = 30,
    universities: list[str] | None = None,
) -> list[Suggestion]:
    """Programmes whose latest cut-off for `method` is at most `score - REACH_MARGIN`.

    Sorted from the most competitive programme the score can reach down to the safest.
    """
    rows = df[(df["method"] == method) & (df["scale"] == scale)]
    if universities:
        rows = rows[rows["university"].isin(universities)]
    # Programmes missing from a university's latest year were closed or renamed, so their
    # last cut-off is out of date.
    latest = rows[rows["year"] == rows.groupby("university")["year"].transform("max")]
    current = set(zip(latest["university"], latest["major_code"], strict=True))

    suggestions = []
    for (university, code), group in rows.groupby(["university", "major_code"]):
        if (university, code) not in current:
            continue
        # A programme can be listed once per subject group; its cut-off is the lowest one.
        per_year = group.groupby("year")["score"].min()
        latest_year = int(per_year.index.max())
        cutoff = float(per_year[latest_year])
        gap = round(score - cutoff, 2)
        if gap < REACH_MARGIN:
            continue
        name = group.loc[group["year"] == latest_year, "major_name"].iloc[0]
        suggestions.append(
            Suggestion(
                university=university,
                major_code=code,
                major_name=name,
                cutoff=cutoff,
                year=latest_year,
                gap=gap,
                level=_level(gap),
                trend=_trend(per_year, per_year.index.to_series()),
                years_seen=len(per_year),
            )
        )
    return sorted(suggestions, key=lambda s: (s.gap, s.university, s.major_code))


def main(argv: list[str] | None = None) -> int:
    import argparse

    from diem_chuan.load import load_scores

    parser = argparse.ArgumentParser(
        prog="python -m diem_chuan.query",
        description="Suggest programmes for a score, based on the latest published cut-offs.",
    )
    parser.add_argument("score", type=float)
    parser.add_argument("--method", default="thpt")
    parser.add_argument("--scale", type=float, default=30)
    parser.add_argument("--university", action="append", help="code, e.g. BKA; repeatable")
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args(argv)

    found = suggest(load_scores(), args.score, args.method, args.scale, args.university)
    for s in found[: args.limit]:
        print(f"[{s.level}] {s.university} {s.major_code} {s.major_name}")
        print(f"    {s.reason()}")
    print(f"{len(found)} programme(s) in reach.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
