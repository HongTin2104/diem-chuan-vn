# Dataset card: diem-chuan-vn

Cut-off scores (điểm chuẩn) of Vietnamese universities, as published by each university.

## Files

| File | One row per | Notes |
|---|---|---|
| `universities.csv` | university | `code` is the ministry code (BKA, QSC, ...) |
| `methods.csv` | admission method | `thpt`, `dgnl_hcm`, `xt_tong_hop`, ... |
| `sources.csv` | official announcement | page link, link to the file (image/PDF) if any, date accessed |
| `scores/<CODE>.csv` | year × major × method × subject groups | one file per university |

### `scores/<CODE>.csv`

| Column | Example | Meaning |
|---|---|---|
| `year` | 2025 | admission year |
| `major_code` | 7480101 | major or programme code, **as printed by the university** (7480104_TT, 75202A1TA) |
| `major_name` | Khoa học Máy tính | name as printed |
| `method` | thpt | key into `methods.csv` |
| `subject_groups` | A00 A01 D01 | space-separated; empty when the source does not list them |
| `score` | 27.2 | cut-off score, dot as decimal separator |
| `scale` | 30 | maximum of the scale the score is on (30, 100, 1200, ...) |
| `source` | qsc-2021-2025 | key into `sources.csv` |
| `note` | | anything the source says that the columns cannot hold |

## Collection

- Every row comes from an announcement on the university's own website, linked in `sources.csv`.
  Aggregator sites are used only to cross-check values, never as the source.
- Most universities publish the table as an image. Values are typed in by hand and then
  read a second time against the image; where an aggregator has the same year, the two are compared.
- Codes, names and scores are kept as published. Codes that change between years (for example
  `7480104_TT` in 2021-2025 and `7480104TT` in 2026) are not merged yet.
- Scores include priority and bonus points when the source says so (UIT does, for all years).

## Coverage

Run `python -m diem_chuan.validate` to check the files. Current coverage:

| University | Years | Methods |
|---|---|---|
| QSC (UIT, VNU-HCM) | 2021-2026 | thpt, dgnl_hcm (2021-2025); xt_tong_hop, scale 100 (2026) |

## Limitations

- Only a few universities so far; contributions are welcome (see CONTRIBUTING.md).
- Subject groups are missing where the announcement does not list them.
- A cut-off score is the lowest admitted score in one year; it is not a prediction for the next.
- Methods change between years (UIT moved to a single combined score on a 100-point scale in 2026),
  so scores are only comparable within the same method and scale.

## License

Data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please credit
"diem-chuan-vn" and the universities as the original publishers. Code: MIT.
