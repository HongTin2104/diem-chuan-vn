from pathlib import Path

import pytest

from diem_chuan.load import load_scores
from diem_chuan.validate import main, validate

UNIVERSITIES = (
    "code,name,short_name,city,ownership,website\n"
    "QSC,Trường Đại học Công nghệ Thông tin,UIT,TP. Hồ Chí Minh,public,https://www.uit.edu.vn\n"
)
METHODS = "method,name_vi,name_en\nthpt,Điểm thi tốt nghiệp THPT,High-school graduation exam\n"
SOURCES = (
    "id,university,years,page_url,file_url,format,accessed\n"
    "qsc-2021-2025,QSC,2021-2025,https://tuyensinh.uit.edu.vn/x,,image,2026-10-30\n"
)
HEADER = "year,major_code,major_name,method,subject_groups,score,scale,source,note\n"
ROW = "2024,7480101,Khoa học Máy tính,thpt,A00 A01,27.3,30,qsc-2021-2025,\n"


def make_data(tmp_path: Path, scores: str = HEADER + ROW, **files: str) -> Path:
    data = tmp_path / "data"
    (data / "scores").mkdir(parents=True)
    contents = {
        "universities.csv": UNIVERSITIES,
        "methods.csv": METHODS,
        "sources.csv": SOURCES,
        "scores/QSC.csv": scores,
    }
    contents.update({name.replace("__", "/") + ".csv": text for name, text in files.items()})
    for name, text in contents.items():
        (data / name).write_text(text, encoding="utf-8", newline="\n")
    return data


def test_valid_data_has_no_errors(tmp_path):
    assert validate(make_data(tmp_path)) == []


def test_load_scores_adds_university_and_types(tmp_path):
    df = load_scores(make_data(tmp_path))
    assert df.loc[0, "university"] == "QSC"
    assert df.loc[0, "major_code"] == "7480101"
    assert df.loc[0, "score"] == 27.3
    assert df.loc[0, "note"] == ""


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("2024,7480101,KHMT,thpt,A00,31,30,qsc-2021-2025,", "outside 0-30"),
        ("2024,7480101,KHMT,thpt,A00,27,5,30,qsc-2021-2025,", "10 fields, expected 9"),
        ('2024,7480101,KHMT,thpt,A00,"27,5",30,qsc-2021-2025,', "with a dot"),
        ("2024,7480101,KHMT,hocba,A00,27,30,qsc-2021-2025,", "not in methods.csv"),
        ("2024,7480101,KHMT,thpt,A0,27,30,qsc-2021-2025,", "should look like A00"),
        ("2024,7480101,KHMT,thpt,A00 A00,27,30,qsc-2021-2025,", "repeats a group"),
        ("2024,7480101,KHMT,thpt,A00,27,30,qsc-2026,", "not in sources.csv"),
        ("2026,7480101,KHMT,thpt,A00,27,30,qsc-2021-2025,", "only covers 2021-2025"),
        ("2010,7480101,KHMT,thpt,A00,27,30,qsc-2021-2025,", "year must be between"),
        ("2024,74801 01,KHMT,thpt,A00,27,30,qsc-2021-2025,", "unexpected characters"),
        ("2024,7480101,,thpt,A00,27,30,qsc-2021-2025,", "major_name is empty"),
        ("2024,7480101,KHMT ,thpt,A00,27,30,qsc-2021-2025,", "trailing spaces"),
        ("2024,7480101,Khoa học,thpt,A00,27,30,qsc-2021-2025,", "NFC"),
    ],
)
def test_bad_score_rows(tmp_path, row, message):
    errors = validate(make_data(tmp_path, HEADER + row + "\n"))
    assert any(message in e for e in errors), errors
    assert errors[0].startswith("data/scores/QSC.csv")


def test_line_numbers_point_at_the_row(tmp_path):
    bad = ROW.replace("27.3", "99")
    errors = validate(make_data(tmp_path, HEADER + ROW.replace("2024", "2023") + bad))
    assert errors == ["data/scores/QSC.csv:3: score 99 is outside 0-30"]


def test_duplicate_rows(tmp_path):
    errors = validate(make_data(tmp_path, HEADER + ROW + ROW))
    assert errors == [
        "data/scores/QSC.csv:3: same year, major_code, method and subject_groups as an earlier row"
    ]


def test_bom_is_rejected(tmp_path):
    data = make_data(tmp_path)
    path = data / "scores" / "QSC.csv"
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    assert any("BOM" in e for e in validate(data))


def test_unknown_university_file(tmp_path):
    data = make_data(tmp_path, scores__XYZ=HEADER + ROW)
    errors = validate(data)
    assert any("XYZ" in e and "not a code" in e for e in errors)
    assert any("belongs to QSC" in e for e in errors)


def test_source_checks(tmp_path):
    sources = (
        "id,university,years,page_url,file_url,format,accessed\n"
        "qsc-2021-2025,QSC,2021-2025,https://x.vn,,image,2026-10-30\n"
        "qsc-2021-2025,ABC,21-25,x.vn,ftp://x,photo,30/10/2026\n"
    )
    errors = validate(make_data(tmp_path, sources=sources))
    for message in ["not in universities.csv", "years must look like"]:
        assert any(message in e for e in errors), errors


@pytest.mark.parametrize(
    ("file_url", "ok"),
    [("https://x.vn/a.png https://x.vn/b.png", True), ("https://x.vn/a.png ftp://x/b", False)],
)
def test_several_file_urls(tmp_path, file_url, ok):
    sources = SOURCES.replace("/x,,image", f"/x,{file_url},image")
    errors = validate(make_data(tmp_path, sources=sources))
    assert (errors == []) is ok, errors


def test_main_exit_codes(tmp_path, capsys):
    assert main([str(make_data(tmp_path / "ok"))]) == 0
    assert "OK: 1 score file" in capsys.readouterr().out
    assert main([str(make_data(tmp_path / "bad", HEADER + ROW.replace("27.3", "99")))]) == 1


def test_university_checks(tmp_path):
    universities = UNIVERSITIES + (
        "qsc,,x,Hà Nội,state,http://x.vn\nQSC,Trường khác,x,Hà Nội,private,https://x.vn\n"
    )
    errors = validate(make_data(tmp_path, universities=universities))
    for message in [
        "data/universities.csv:3: code 'qsc' is not three capital letters",
        "data/universities.csv:3: name is empty",
        "data/universities.csv:3: ownership must be one of",
        "data/universities.csv:3: website must start with https://",
        "data/universities.csv: code QSC is listed more than once",
    ]:
        assert any(e.startswith(message) for e in errors), errors


def test_duplicate_method(tmp_path):
    methods = METHODS + "thpt,Thi THPT,Exam\n"
    errors = validate(make_data(tmp_path, methods=methods))
    assert errors == ["data/methods.csv: method thpt is listed more than once"]


def test_every_source_field_is_checked(tmp_path):
    sources = SOURCES + "qsc-2021-2025,QSC,2024,x.vn,ftp://x,photo,30/10/2026\n"
    errors = validate(make_data(tmp_path, sources=sources))
    assert [e.split(": ", 1)[1] for e in errors] == [
        "page_url must be a link to the official page",
        "file_url must be empty or links separated by spaces",
        "format must be one of ['html', 'image', 'pdf', 'xlsx']",
        "accessed must be a date like 2026-10-30",
        "id qsc-2021-2025 is used more than once",
    ]


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("năm".encode("cp1258"), "file is not valid UTF-8"),
        (b"", "columns must be exactly"),
        (b"year,score\n2024,27\n", "columns must be exactly"),
        (HEADER.encode(), "file has no rows"),
    ],
)
def test_unreadable_score_files(tmp_path, content, message):
    data = make_data(tmp_path)
    (data / "scores" / "QSC.csv").write_bytes(content)
    errors = validate(data)
    assert len(errors) == 1 and errors[0].startswith(f"data/scores/QSC.csv: {message}"), errors


@pytest.mark.parametrize("scale", ["0", "x"])
def test_bad_scale(tmp_path, scale):
    row = ROW.replace(",30,", f",{scale},")
    errors = validate(make_data(tmp_path, HEADER + row))
    assert errors == ["data/scores/QSC.csv:2: scale must be a positive number, e.g. 30"]


def test_year_must_be_a_number(tmp_path):
    errors = validate(make_data(tmp_path, HEADER + ROW.replace("2024", "năm 2024")))
    assert len(errors) == 1 and "year must be between" in errors[0]


def test_broken_reference_files_skip_their_checks(tmp_path):
    data = make_data(tmp_path, universities="code\nQSC\n", methods="", sources="id\n")
    errors = validate(data)
    assert {e.split(":")[0] for e in errors} == {
        "data/universities.csv",
        "data/methods.csv",
        "data/sources.csv",
        "data/scores/QSC.csv",
    }
