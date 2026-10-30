"""Column layout of the CSV files under data/."""

import re

UNIVERSITY_COLUMNS = ["code", "name", "short_name", "city", "ownership", "website"]
METHOD_COLUMNS = ["method", "name_vi", "name_en"]
SOURCE_COLUMNS = ["id", "university", "years", "page_url", "file_url", "format", "accessed"]
SCORE_COLUMNS = [
    "year",
    "major_code",
    "major_name",
    "method",
    "subject_groups",
    "score",
    "scale",
    "source",
    "note",
]

OWNERSHIPS = {"public", "private", "foreign"}
SOURCE_FORMATS = {"html", "pdf", "image", "xlsx"}

# Ministry university codes: three letters, e.g. BKA, QSC.
UNIVERSITY_CODE_RE = re.compile(r"^[A-Z]{3}$")
# Published as-is: 7480201, 7480104_TT, 75202A1TA, IT-E10 ...
MAJOR_CODE_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z_-]*$")
# A00, D01, DD2, K01 ...
SUBJECT_GROUP_RE = re.compile(r"^[A-Z][A-Z0-9]\d$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
YEARS_RE = re.compile(r"^(\d{4})(?:-(\d{4}))?$")

FIRST_YEAR = 2015
