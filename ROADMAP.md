# Roadmap

Where diem-chuan-vn is going, and why. Each release is a
[milestone](https://github.com/HongTin2104/diem-chuan-vn/milestones) with its issues; pick one,
comment on it, and open a pull request.

## The goal

A student choosing their nguyện vọng should be able to answer three questions with data they can
check: *where do I stand this year*, *what will the cut-off be*, and *which list of choices gives me
the best chance*. Today the dataset covers 3 universities; every step below either adds data or
turns the data into a better answer to one of those questions.

## Releases

| Release | Target | What it adds | Why |
|---|---|---|---|
| [v0.3](https://github.com/HongTin2104/diem-chuan-vn/milestone/1) | Nov 2026 | About 10 more universities, a subject-group table (#3), programme codes linked across years (#4) | Most visitors look for their own university first. Trends and forecasts need enough programmes and years. |
| [v0.4](https://github.com/HongTin2104/diem-chuan-vn/milestone/2) | Dec 2026 | Score distributions per subject group (#22), cut-offs as ranks, suggestions by rank (#23) | 27.0 in an easy year is not 27.0 in a hard year. A rank ("top 4% of A00") is comparable across years. |
| [v0.5](https://github.com/HongTin2104/diem-chuan-vn/milestone/3) | Jan 2027 | Cut-off forecast with a published backtest error (#24), an ordered list of nguyện vọng (#25) | The cut-off is unknown when students choose. A forecast is only useful if we say how often it is right. |
| [v0.6](https://github.com/HongTin2104/diem-chuan-vn/milestone/4) | Mar 2027 | Watch the official pages for changes (#26), draft rows from an announcement image (#27) | 2027 cut-offs should be in the dataset within a day, and adding a university should take minutes. |

Dates are targets, not promises. The wide launch is planned after v0.5, before the 2027
application season (March to July).

## Principles that do not change

- Every row comes from the university's own announcement, linked in `sources.csv`.
- Forecasts and ranks come with their method and their measured error, in a report that a script
  regenerates.
- No personal data: score distributions are stored as aggregated counts only.
- Data stays CC BY 4.0, code MIT.

## Not planned

- Scraping aggregator sites as a source.
- Predictions without a backtest.
- Accounts, logins or storing what users type into the app.

## Tiếng Việt

Mục tiêu: giúp học sinh trả lời ba câu hỏi bằng dữ liệu kiểm chứng được: *năm nay mình đứng ở đâu*,
*điểm chuẩn năm nay khoảng bao nhiêu*, và *nên xếp nguyện vọng thế nào*.

- **v0.3 (11/2026):** thêm khoảng 10 trường, bảng tổ hợp môn, nối mã ngành đổi qua các năm.
- **v0.4 (12/2026):** phổ điểm theo tổ hợp, đổi điểm chuẩn ra thứ hạng ("top 4% khối A00").
- **v0.5 (01/2027):** dự đoán điểm chuẩn kèm sai số đo bằng backtest, gợi ý thứ tự nguyện vọng.
- **v0.6 (03/2027):** tự theo dõi trang công bố của các trường, công cụ đọc ảnh thông báo để nhập liệu nhanh.

Muốn góp sức: chọn một issue trong [milestones](https://github.com/HongTin2104/diem-chuan-vn/milestones),
bình luận để nhận việc rồi mở pull request. Thêm điểm chuẩn của trường bạn là cách bắt đầu dễ nhất.
