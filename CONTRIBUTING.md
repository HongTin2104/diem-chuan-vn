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
   - `subject_groups` stays empty if the announcement does not list them.
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

- Python 3.11+, `ruff check .` and `ruff format --check .` must pass.
- Keep pull requests small and focused; open an issue first for anything larger.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):
  `data: add FTU 2025`, `feat(query): ...`, `fix(validate): ...`.

## Tiếng Việt

Cách đóng góp có ích nhất là thêm dữ liệu: điểm chuẩn của **một trường trong một năm** là đủ một pull
request, không cần biết code.

1. Tìm thông báo điểm chuẩn **trên website chính thức của trường**. Không lấy từ trang tổng hợp hay báo.
2. Thêm một dòng nguồn vào `data/sources.csv`.
3. Nếu là trường mới, thêm trường vào `data/universities.csv` (mã trường theo Bộ GD&ĐT).
4. Nhập điểm vào `data/scores/<MÃ_TRƯỜNG>.csv`. Giữ nguyên mã và tên ngành như trong thông báo. Số
   thập phân dùng dấu chấm. Ghi rõ thang điểm.
5. Chạy `python -m diem_chuan.validate` và `pytest -q`, sửa đến khi không còn lỗi.
6. Trong pull request, ghi bạn đã kiểm tra thế nào, ví dụ "nhập từ ảnh, đã soát lại từng dòng".
   Không tự điền số không có trong nguồn.

Nếu gặp khó khăn, cứ mở pull request dở dang hoặc hỏi trong issue, mình sẽ hỗ trợ.
