---
license: cc-by-4.0
language:
- vi
pretty_name: Vietnamese university cut-off scores (điểm chuẩn)
size_categories:
- $size_category
tags:
- education
- university-admission
- vietnam
- tabular
configs:
- config_name: default
  data_files: $parquet
---

# diem-chuan-vn: Vietnamese university cut-off scores

Cut-off scores (điểm chuẩn) of Vietnamese universities, $first_year-$last_year, as published by each
university. $rows rows from $universities universities and $sources official announcements; every row
links to the announcement it comes from.

Source code, raw CSV files and the full data card: https://github.com/HongTin2104/diem-chuan-vn
(this file was generated from release v$version).

## Load

```python
from datasets import load_dataset

ds = load_dataset("$hf_repo", split="train")
```

or with pandas:

```python
import pandas as pd

df = pd.read_parquet("hf://datasets/$hf_repo/$parquet")
```

## Columns

| Column | Example | Meaning |
|---|---|---|
| `university` | BKA | ministry code of the university |
| `university_name`, `university_short_name`, `city` | Đại học Bách khoa Hà Nội, HUST, Hà Nội | |
| `year` | 2025 | admission year |
| `major_code` | 7480101 | programme code **as printed by the university** |
| `major_name` | Khoa học Máy tính | name as printed |
| `method` | thpt | admission method key |
| `method_name_vi`, `method_name_en` | Điểm thi tốt nghiệp THPT | |
| `subject_groups` | A00 A01 D01 | space-separated; empty when the source does not list them |
| `score` | 27.2 | cut-off score |
| `scale` | 30 | maximum of the scale the score is on (30, 100, 1200, ...) |
| `note` | | anything the source says that the columns cannot hold |
| `source` | bka-2025 | id of the announcement |
| `source_page_url`, `source_file_url`, `source_accessed` | | where the values were read, and when |

## How it was collected

Only the university's own announcement is used as a source. HTML tables are read by an extractor
that can be re-run; images and scanned PDFs are typed in by hand, read a second time from enlarged
crops, and compared with an aggregator where one has the same year. The check done for each source
is listed in
[DATASET.md](https://github.com/HongTin2104/diem-chuan-vn/blob/main/data/DATASET.md).

## Limitations

- Compare scores only within the same `method` and `scale`.
- Codes and names are kept as published. A programme whose code changes between years appears under
  both codes.
- Only some universities are covered so far. Contributions are welcome on GitHub.

## License and citation

Data: CC BY 4.0. Code: MIT. If you use the data, please cite it as described in
[CITATION.cff](https://github.com/HongTin2104/diem-chuan-vn/blob/main/CITATION.cff).
