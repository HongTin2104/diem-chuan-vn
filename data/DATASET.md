# Dataset card: diem-chuan-vn

Cut-off scores (điểm chuẩn) of Vietnamese universities, as published by each university.

## Files

| File | One row per | Notes |
|---|---|---|
| `universities.csv` | university | `code` is the ministry code (BKA, QSC, ...) |
| `methods.csv` | admission method | `thpt`, `dgnl_hcm`, `xt_tong_hop`, ... |
| `sources.csv` | official announcement | page link, links to the files (images/PDF, space-separated) if any, date accessed |
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
- HTML tables are read by an extractor in `src/diem_chuan/sources/` (`python -m diem_chuan.sources
  bka-2023`), so they can be re-extracted.
- Most universities publish the table as an image. Values are typed in by hand and then
  read a second time from enlarged crops of the image; where an aggregator has the same year, the
  two are compared. The second read has caught real typing errors (HUST 2024, FL1).
- Codes, names and scores are kept as published. Codes that change between years (for example
  `7480104_TT` in 2021-2025 and `7480104TT` in 2026, or HUST `TE-EP` and `TEEP`) are not merged yet.
  "(mới)" after a 2026 HUST programme name is moved to `note`.
- Scores include priority and bonus points when the source says so (UIT does, for all years).
- NEU (2025-2026) publishes a single cut-off per programme on the 30-point exam scale that applies to
  every admission method; it is stored as `thpt` with a note. Codes such as CLC1 or TT1 group several
  programmes; the name lists them as published.
- HUST lists the thinking-skills test as subject group K00; it is stored as method `tsa` with
  no subject group. From 2025 HUST publishes one score per programme for a base group (A00 or
  D01) plus a table of offsets (up to 0.5) for other groups; the base group is stored and the
  offsets are only mentioned in `note`.

### Checks done per source

| Source | How it was entered | Check |
|---|---|---|
| qsc-2021-2025 | typed from image | second read: 124/124 cells agree |
| qsc-2026 | typed from image | aggregator: 19/19 agree |
| bka-2023 | HTML extractor | none needed |
| bka-2024 | typed from image | second read at 2x: 1 of 128 cells corrected |
| bka-2025 | typed from image | second read: 260/260 agree |
| kha-2025 | typed from page images | second read: 73/73 agree |
| kha-2026 | typed from scanned PDF | aggregator: all 88 scores present (it also lists each programme inside the grouped codes CLC1-3 and TT1-2 separately) |
| bka-2026 | typed from image | aggregator: 68/68 THPT scores agree; counts stated in the article (3 programmes above 29, 14 above 28, 30 above 27, 53 above 24) agree; second read of the other 204 cells agrees |

## Coverage

Run `python -m diem_chuan.validate` to check the files. Current coverage:

| University | Years | Methods |
|---|---|---|
| QSC (UIT, VNU-HCM) | 2021-2026 | thpt, dgnl_hcm (2021-2025); xt_tong_hop, scale 100 (2026) |
| BKA (HUST) | 2023-2026 | thpt, tsa (2023-2026); xttn_chung_chi, xttn_ho_so (2025-2026) |
| KHA (NEU) | 2025-2026 | thpt: one score per programme, converted to the 30-point scale and used for every method |

## Limitations

- Only a few universities so far; contributions are welcome (see CONTRIBUTING.md).
- Subject groups are missing where the announcement does not list them.
- A cut-off score is the lowest admitted score in one year; it is not a prediction for the next.
- Methods change between years (UIT moved to a single combined score on a 100-point scale in 2026),
  so scores are only comparable within the same method and scale.

## License

Data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please credit
"diem-chuan-vn" and the universities as the original publishers. Code: MIT.
