# Contributing

Thanks for helping. Data is the most useful contribution: one university and one year is a
complete pull request, and you do not need to write code for it.

By taking part you agree to the [code of conduct](CODE_OF_CONDUCT.md).

*Tiếng Việt ở cuối trang.*

## Add a university or a year

1. **Find the official announcement** on the university's own website (not an aggregator, not a
   newspaper). Comment on the matching issue, or open one, so two people do not do the same year.
2. **Add the source** as one line in `data/sources.csv`:

   ```
   id,university,years,page_url,file_url,format,accessed
   nth-2025,NTH,2025,https://ftu.edu.vn/...,https://ftu.edu.vn/.../diem-chuan.jpg,image,2026-11-02
   ```

   - `id`: lower-case university code, a dash, the year (or `2021-2025` for a multi-year table).
   - `file_url`: links to the image or PDF, space-separated; empty for an HTML table.
   - `format`: `html`, `pdf`, `image` or `xlsx`.
3. **Add the university** to `data/universities.csv` if it is new. `code` is the ministry code
   (BKA, KHA, NTH, QSB...).
4. **Add the scores** to `data/scores/<CODE>.csv`, one row per programme, method and year:

   ```
   year,major_code,major_name,method,subject_groups,score,scale,source,note
   2025,NTH01,Kinh tế,thpt,A00 A01 D01,28.5,30,nth-2025,
   ```

   - Copy codes and names exactly as published.
   - Use a dot for decimals (`27.5`, not `27,5`).
   - `method` must exist in `data/methods.csv`. If the university uses a new method, add it
     there with a Vietnamese and an English name.
   - `scale` is the maximum of the scale the score is on: 30, 40, 100, 150, 1200...
   - `subject_groups` stays empty if the announcement does not list them. Every group must be in
     `data/subject_groups.csv`; if it is not, add it with its subjects (`Toán; Vật lý; Tiếng Đức`)
     and a link to an official page that defines it, such as the university's admission scheme.
   - Put anything the columns cannot hold in `note`.
5. **Check** before opening the pull request:

   ```bash
   pip install -e ".[dev]"
   python -m diem_chuan.validate
   pytest -q
   ```

   The validator prints `file:line: problem` for anything it does not accept.
6. **Describe the check you did** in the pull request, for example "typed from the image, then read
   again row by row" or "compared with an aggregator: 60/60 agree". Never fill a gap with a value
   you did not find in the source.

Excel tip: Excel often saves CSV with a byte-order mark or a different encoding. Save as
"CSV UTF-8" and the validator will tell you if something is still off.

## Add an extractor

If the announcement is an HTML table or a text PDF, an extractor is better than typing: it can be
re-run. Add `src/diem_chuan/sources/<code>.py` with an `EXTRACTORS` dict (see `bka.py`), use
`diem_chuan.crawl.fetch` (robots.txt, delay, cache), and add a test that runs on a small fixed
table so the test needs no network. Then:

```bash
python -m diem_chuan.sources nth-2025
```

## Code changes

- Python 3.11+. Run `pre-commit install` once; ruff and a few file checks then run on every
  commit. `pre-commit run --all-files` runs them by hand.
- New code comes with tests. CI fails below 95% coverage (`pytest --cov`).
- Keep pull requests small and focused; open an issue first for anything larger.
- Commit messages and pull request titles follow
  [Conventional Commits](https://www.conventionalcommits.org/):
  `data: add FTU 2025`, `feat(query): ...`, `fix(validate): ...`.

## What runs on a pull request

| Check | What it does |
|---|---|
| CI / data | `python -m diem_chuan.validate`, plus a table of the data files changed |
| CI / lint | the pre-commit hooks: ruff, ruff format, YAML/TOML, large files, private keys |
| CI / test | pytest on Python 3.11, 3.12 and 3.13 with the coverage threshold |
| CI / docker | builds the image and validates the data inside it |
| CodeQL | static security analysis of the Python code and the workflows |
| Pull request / title | the title follows Conventional Commits |
| Pull request / label | adds `data`, `extractor`, `app`, `documentation` or `ci` from the files changed |

Pull requests from a first-time contributor wait for a maintainer to approve the workflow run.
Dependabot opens monthly pull requests for dependency updates.

## Releasing (maintainers)

1. Open a pull request titled `release: vX.Y.Z` that sets the version in `pyproject.toml` and
   `CITATION.cff` and moves the `Unreleased` changelog entries under the new version. Merge it once
   CI is green.
2. `gh release create vX.Y.Z --target main --notes-file <notes>`. The Release workflow attaches
   `diem_chuan.parquet` to the release and keeps `dist/hf/` as the `hf-dataset` artifact.
3. Upload the same files to Hugging Face (`pip install huggingface_hub`, then `hf auth login` once):

   ```bash
   git checkout vX.Y.Z
   python -m diem_chuan.export
   hf upload HongTin2104/diem-chuan-vn dist/hf . --repo-type dataset --commit-message "vX.Y.Z"
   ```

## Tiếng Việt

Cách đóng góp có ích nhất là thêm dữ liệu: điểm chuẩn của **một trường trong một năm** là đủ một pull
request, không cần biết code.

1. Tìm thông báo điểm chuẩn **trên website chính thức của trường**. Không lấy từ trang tổng hợp hay báo.
2. Thêm một dòng nguồn vào `data/sources.csv`.
3. Nếu là trường mới, thêm trường vào `data/universities.csv` (mã trường theo Bộ GD&ĐT).
4. Nhập điểm vào `data/scores/<MÃ_TRƯỜNG>.csv`. Giữ nguyên mã và tên ngành như trong thông báo. Số
   thập phân dùng dấu chấm. Ghi rõ thang điểm. Tổ hợp nào chưa có trong `data/subject_groups.csv`
   thì thêm vào, kèm các môn và link tới trang chính thức định nghĩa tổ hợp đó.
5. Chạy `python -m diem_chuan.validate` và `pytest -q`, sửa đến khi không còn lỗi. Khi mở pull
   request, CI sẽ tự chạy lại các bước này, cùng với lint, CodeQL và kiểm tra tiêu đề (theo dạng
   `data: add FTU 2025`).
6. Trong pull request, ghi bạn đã kiểm tra thế nào, ví dụ "nhập từ ảnh, đã soát lại từng dòng".
   Không tự điền số không có trong nguồn.

Nếu gặp khó khăn, cứ mở pull request dở dang hoặc hỏi trong issue, mình sẽ hỗ trợ.
