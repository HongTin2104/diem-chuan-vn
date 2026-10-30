"""Hanoi University of Science and Technology (HUST, ĐHBK Hà Nội)."""

from diem_chuan.crawl import fetch, html_tables, parse_groups, parse_score
from diem_chuan.sources import Row

PAGE_2023 = "https://ts.hust.edu.vn/tin-tuc/diem-chuan-dai-hoc-bach-khoa-ha-noi-nam-2023"
HEADER = ["STT", "Mã tuyển sinh", "Tên chương trình đào tạo", "Tổ hợp", "Điểm chuẩn"]


def _table_rows(table: list[list[str]], method: str, scale: str) -> list[Row]:
    if table[0] != HEADER:
        raise ValueError(f"unexpected header {table[0]}")
    rows = []
    for stt, code, name, groups, score in table[1:]:
        if not stt.isdigit():
            raise ValueError(f"unexpected row {stt, code, name}")
        rows.append(
            {
                "year": "2023",
                "major_code": code,
                "major_name": name,
                "method": method,
                # K00 only names the thinking-skills test, which `method` already says.
                "subject_groups": "" if groups == "K00" else parse_groups(groups),
                "score": parse_score(score),
                "scale": scale,
            }
        )
    return rows


def rows_2023() -> list[Row]:
    tables = html_tables(fetch(PAGE_2023).decode("utf-8"))
    tsa, thpt = (t for t in tables if t and t[0] == HEADER)
    return _table_rows(thpt, "thpt", "30") + _table_rows(tsa, "tsa", "100")


EXTRACTORS = {"bka-2023": rows_2023}
