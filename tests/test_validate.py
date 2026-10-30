from pathlib import Path

import pytest

from diem_chuan.load import load_scores, load_subject_groups
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
SUBJECT_GROUPS = (
    "code,subjects,source_url\n"
    "A00,Toán; Vật lý; Hóa học,https://x.vn/to-hop\n"
    "A01,Toán; Vật lý; Tiếng Anh,https://x.vn/to-hop\n"
)
HEADER = "year,major_code,major_name,method,subject_groups,score,scale,source,note\n"
ROW = "2024,7480101,Khoa học Máy tính,thpt,A00 A01,27.3,30,qsc-2021-2025,\n"


def make_data(tmp_path: Path, scores: str = HEADER + ROW, **files: str) -> Path:
    data = tmp_path / "data"
    (data / "scores").mkdir(parents=True)
    contents = {
        "universities.csv": UNIVERSITIES,
        "methods.csv": METHODS,
        "subject_groups.csv": SUBJECT_GROUPS,
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
        ("2024,7480101,KHMT,thpt,A00 X01,27,30,qsc-2021-2025,", "X01 is not in subject_groups.csv"),
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
    ("source_id", "years"),
    [
        ("QSC-2021-2025", "2021-2025"),
        ("qsc-2021_2025", "2021-2025"),
        ("qsc-2024", "2021-2025"),
        ("other-2024", "2024"),
    ],
)
def test_source_id_matches_university_and_years(tmp_path, source_id, years):
    sources = SOURCES.replace("qsc-2021-2025,QSC,2021-2025", f"{source_id},QSC,{years}")
    scores = HEADER + ROW.replace("qsc-2021-2025", source_id)
    errors = validate(make_data(tmp_path, scores, sources=sources))
    assert errors == [f"data/sources.csv:2: id must be 'qsc-{years}'"]


@pytest.mark.parametrize("years", ["2024", "2021-2025"])
def test_source_id_accepts_single_year_and_range(tmp_path, years):
    source_id = f"qsc-{years}"
    sources = SOURCES.replace("qsc-2021-2025,QSC,2021-2025", f"{source_id},QSC,{years}")
    scores = HEADER + ROW.replace("qsc-2021-2025", source_id)
    assert validate(make_data(tmp_path, scores, sources=sources)) == []


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


RENAMED_SCORES = (
    HEADER
    + "2024,7480104_TT,HTTT,thpt,A00,25,30,qsc-2021-2025,\n"
    + "2025,7480104TT,HTTT,thpt,A00,26,30,qsc-2021-2025,\n"
    + "2025,7480101,KHMT,thpt,A00,27,30,qsc-2021-2025,\n"
)
ALIASES = "university,code,same_as\n"


def test_valid_alias_joins_the_years(tmp_path):
    data = make_data(
        tmp_path, RENAMED_SCORES, programme_aliases=ALIASES + "QSC,7480104_TT,7480104TT\n"
    )
    assert validate(data) == []
    df = load_scores(data)
    assert list(df["programme"]) == ["7480104TT", "7480104TT", "7480101"]


def test_without_aliases_file_programme_is_the_code(tmp_path):
    df = load_scores(make_data(tmp_path, RENAMED_SCORES))
    assert list(df["programme"]) == list(df["major_code"])


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("XYZ,A,B", "university 'XYZ' has no scores file"),
        ("QSC,7480104_TT,NOPE", "NOPE is not a major_code in scores/QSC.csv"),
        ("QSC,7480104TT,7480104TT", "code and same_as are the same"),
        ("QSC,7480104TT,7480104_TT", "7480104TT must only appear in years before 7480104_TT"),
        ("QSC,7480101,7480104TT", "7480101 must only appear in years before 7480104TT"),
    ],
)
def test_bad_alias(tmp_path, row, message):
    data = make_data(tmp_path, RENAMED_SCORES, programme_aliases=ALIASES + row + "\n")
    assert validate(data) == [f"data/programme_aliases.csv:2: {message}"]


def test_alias_chain_and_duplicate(tmp_path):
    aliases = (
        ALIASES + "QSC,7480104_TT,7480104TT\nQSC,7480104_TT,7480104TT\nQSC,7480101,7480104_TT\n"
    )
    errors = validate(make_data(tmp_path, RENAMED_SCORES, programme_aliases=aliases))
    assert "data/programme_aliases.csv:3: this code is already listed" in errors
    assert (
        "data/programme_aliases.csv:4: same_as 7480104_TT is itself an old code; "
        "point to the current one"
    ) in errors


def test_aliases_with_wrong_columns(tmp_path):
    errors = validate(make_data(tmp_path, programme_aliases="code,same_as\nA,B\n"))
    assert errors == [
        "data/programme_aliases.csv: columns must be exactly: university,code,same_as"
    ]


def test_load_subject_groups(tmp_path):
    df = load_subject_groups(make_data(tmp_path))
    assert df.set_index("code").loc["A01", "subjects"] == "Toán; Vật lý; Tiếng Anh"


def test_subject_groups_with_wrong_columns(tmp_path):
    errors = validate(make_data(tmp_path, subject_groups="code,subjects\nA00,Toán\n"))
    assert errors[0].startswith("data/subject_groups.csv: columns must be exactly")
    # Without a readable table, every group used in the scores is unknown.
    assert errors[1:] == [
        "data/scores/QSC.csv:2: subject group A00 is not in subject_groups.csv",
        "data/scores/QSC.csv:2: subject group A01 is not in subject_groups.csv",
    ]


def test_every_subject_group_field_is_checked(tmp_path):
    groups = SUBJECT_GROUPS + "A0,Toán,x.vn/to-hop\nA00,Toán;; Lý,https://x.vn\n"
    errors = validate(make_data(tmp_path, subject_groups=groups))
    assert [e.split(": ", 1)[1] for e in errors] == [
        "code 'A0' should look like A00 or D01",
        "subjects must list the subjects separated by '; '",
        "source_url must be a link to where the group is defined",
        "subjects must list the subjects separated by '; '",
        "code A00 is listed more than once",
    ]


def test_every_source_field_is_checked(tmp_path):
    sources = SOURCES + "qsc-2021-2025,QSC,2024,x.vn,ftp://x,photo,30/10/2026\n"
    errors = validate(make_data(tmp_path, sources=sources))
    assert [e.split(": ", 1)[1] for e in errors] == [
        "id must be 'qsc-2024'",
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
