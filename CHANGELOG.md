# Changelog

## 0.1.0 (2026-10-30)

First release.

### Data
- 1,088 cut-off scores from 8 official announcements:
  HUST (BKA) 2023-2026, NEU (KHA) 2025-2026, UIT (QSC) 2021-2026.
- Every row links to its source; `data/DATASET.md` lists the check done for each source.

### Code
- `diem_chuan.validate`: checks every data file and reports `file:line: problem`; runs in CI.
- `diem_chuan.crawl` and `diem_chuan.sources`: polite fetching (robots.txt, delay, cache) and an
  extractor for HUST's HTML tables.
- `diem_chuan.query`: programme history, and suggestions for a score with a reason for each.
- Streamlit demo (`app/app.py`) and Dockerfile.
