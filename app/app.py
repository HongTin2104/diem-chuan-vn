"""Streamlit demo: suggest programmes for a score, and look up a programme's history."""

import altair as alt
import pandas as pd
import streamlit as st

from diem_chuan import load_scores, load_sources, load_universities
from diem_chuan.load import load_methods
from diem_chuan.query import history, suggest

REPO = "https://github.com/HongTin2104/diem-chuan-vn"
LEVEL_ORDER = ["thử thách", "vừa sức", "an toàn"]

st.set_page_config(page_title="Điểm chuẩn đại học", layout="wide")


@st.cache_data
def data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return load_scores(), load_universities(), load_methods(), load_sources()


scores, universities, methods, sources = data()
uni_name = dict(zip(universities["code"], universities["short_name"], strict=True))
method_name = dict(zip(methods["method"], methods["name_vi"], strict=True))

st.title("Điểm chuẩn đại học")
st.caption(
    f"{len(scores):,} dòng điểm chuẩn của {scores['university'].nunique()} trường, "
    f"{scores['year'].min()}-{scores['year'].max()}. Mỗi dòng có link tới thông báo chính thức. "
    f"Dữ liệu mở: [{REPO.removeprefix('https://')}]({REPO})"
)

suggest_tab, lookup_tab = st.tabs(["Gợi ý ngành theo điểm", "Tra cứu một ngành"])

with suggest_tab:
    options = (
        scores.groupby(["method", "scale"])
        .size()
        .reset_index()[["method", "scale"]]
        .values.tolist()
    )
    left, mid, right = st.columns([2, 1, 2])
    method, scale = left.selectbox(
        "Phương thức",
        options,
        index=options.index(["thpt", 30.0]),
        format_func=lambda o: f"{method_name.get(o[0], o[0])} (thang {o[1]:g})",
    )
    score = mid.number_input(
        "Điểm của bạn",
        min_value=0.0,
        max_value=float(scale),
        value=min(25.0, float(scale)),
        step=0.25,
    )
    picked = right.multiselect(
        "Trường", sorted(uni_name), format_func=lambda c: f"{uni_name[c]} ({c})"
    )

    found = suggest(scores, score, method, scale, picked or None)
    if not found:
        st.info("Chưa có ngành nào trong tầm điểm này với phương thức đã chọn.")
    else:
        table = pd.DataFrame(
            {
                "Mức": [s.level for s in found],
                "Trường": [uni_name.get(s.university, s.university) for s in found],
                "Mã": [s.major_code for s in found],
                "Ngành / chương trình": [s.major_name for s in found],
                "Điểm chuẩn": [s.cutoff for s in found],
                "Năm": [s.year for s in found],
                "Chênh lệch": [s.gap for s in found],
                "Vì sao": [s.reason() for s in found],
            }
        )
        counts = table["Mức"].value_counts()
        st.write(
            " · ".join(f"**{counts.get(level, 0)}** {level}" for level in LEVEL_ORDER)
            + " (thử thách: thấp hơn tối đa 1 điểm; an toàn: cao hơn từ 1 điểm)"
        )
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            column_config={
                "Điểm chuẩn": st.column_config.NumberColumn(format="%.2f"),
                "Chênh lệch": st.column_config.NumberColumn(format="%+.2f"),
                "Năm": st.column_config.NumberColumn(format="%d"),
            },
        )
    st.caption(
        "Điểm chuẩn là điểm thấp nhất trúng tuyển của năm đó, không phải dự đoán cho năm sau. "
        "Chỉ so sánh trong cùng phương thức và cùng thang điểm."
    )

with lookup_tab:
    left, right = st.columns([1, 3])
    uni = left.selectbox(
        "Trường", sorted(uni_name), format_func=lambda c: f"{uni_name[c]} ({c})", key="lookup_uni"
    )
    rows = scores[scores["university"] == uni]
    latest = rows.sort_values("year").drop_duplicates("major_code", keep="last")
    labels = dict(zip(latest["major_code"], latest["major_name"], strict=True))
    code = right.selectbox(
        "Ngành / chương trình",
        sorted(labels, key=labels.get),
        format_func=lambda c: f"{labels[c]} ({c})",
    )

    picked_rows = rows[rows["major_code"] == code]
    for method in picked_rows["method"].unique():
        h = history(scores, uni, code, method)
        scale = h["scale"].iloc[0]
        st.subheader(f"{method_name.get(method, method)} (thang {scale:g})")
        if h["year"].nunique() > 1:
            chart = (
                alt.Chart(h)
                .mark_line(point=True)
                .encode(
                    x=alt.X("year:O", title="Năm"),
                    y=alt.Y("score:Q", title="Điểm chuẩn", scale=alt.Scale(zero=False)),
                    tooltip=["year", "score", "subject_groups"],
                )
                .properties(height=220)
            )
            st.altair_chart(chart, width="stretch")
        st.dataframe(
            h.rename(
                columns={
                    "year": "Năm",
                    "score": "Điểm chuẩn",
                    "scale": "Thang",
                    "subject_groups": "Tổ hợp",
                    "note": "Ghi chú",
                }
            ),
            hide_index=True,
            width="stretch",
            column_config={"Năm": st.column_config.NumberColumn(format="%d")},
        )

    used = sources[sources["id"].isin(picked_rows["source"])].sort_values("years")
    st.markdown("**Nguồn**")
    for _, src in used.iterrows():
        st.markdown(f"- {src['years']}: [thông báo chính thức]({src['page_url']})")
