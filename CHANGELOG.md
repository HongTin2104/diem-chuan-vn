# Changelog

## 0.1.1 (2026-10-30)

No data changes.

### Fixed
- `diem_chuan.validate` checks that each source id is `<lower-case university>-<years>`, so a
  misnamed source is reported instead of passing silently (#13, thanks @Golden007-prog).

### Project
- Tests cover fetching, robots.txt, every validator check and the CLIs; CI fails below 95% coverage.
- CI runs on Python 3.11-3.13 with CodeQL, pre-commit lint, PR title and label checks, and a
  summary of data changes on each pull request.
- Citation file, code of conduct, security policy, contributing guide and a first EDA notebook.

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
