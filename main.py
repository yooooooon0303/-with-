import streamlit as st
import pandas as pd

st.set_page_config(page_title="도시 열섬현상 분석", layout="wide")

st.title("🌡️ 서울 vs 양평 기온 비교")
st.subheader("도시 열섬현상(Urban Heat Island) 분석 — 2025년 시간별 기온 데이터")


@st.cache_data
def load_data():
    seoul = pd.read_csv("서울_기온.csv", encoding="cp949")
    yangpyeong = pd.read_csv("양평_기온.csv", encoding="cp949")

    def preprocess(df, region_name):
        # '기온'이 포함된 열을 찾음 (인코딩에 따라 '기온(°C)' 표기가 달라질 수 있음)
        temp_col = [c for c in df.columns if "기온" in c][0]
        df = df[["일시", temp_col]].rename(columns={temp_col: region_name})
        df["일시"] = pd.to_datetime(df["일시"])
        return df

    seoul = preprocess(seoul, "서울")
    yangpyeong = preprocess(yangpyeong, "양평")

    # 두 지역의 같은 시각 데이터만 병합
    merged = pd.merge(seoul, yangpyeong, on="일시", how="inner")
    merged["기온차(서울-양평)"] = merged["서울"] - merged["양평"]
    return merged


df = load_data()

# ── 요약 지표 ──────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("서울 연평균 기온", f"{df['서울'].mean():.1f} °C")
col2.metric("양평 연평균 기온", f"{df['양평'].mean():.1f} °C")
col3.metric("연평균 기온차 (서울-양평)", f"{df['기온차(서울-양평)'].mean():.2f} °C")

st.divider()

# ── ① 1년간 기온 변화 (선그래프) ──────────────────────────
st.header("① 1년간 두 지역의 기온 변화")

view_option = st.radio(
    "표시 방식 선택",
    ["일평균 (보기 편함)", "시간별 원자료 (8,760개)"],
    horizontal=True,
)

if view_option.startswith("일평균"):
    chart_df = (
        df.set_index("일시")[["서울", "양평"]]
        .resample("D")
        .mean()
    )
else:
    chart_df = df.set_index("일시")[["서울", "양평"]]

st.line_chart(chart_df, x_label="일시", y_label="기온 (°C)")

st.divider()

# ── ② 시각별 평균 기온차 (막대그래프) ─────────────────────
st.header("② 시각(0~23시)별 평균 기온차 (서울 − 양평)")
st.caption("열섬현상은 보통 밤~새벽 시간대에 기온차가 크게 나타납니다.")

hourly_diff = (
    df.groupby(df["일시"].dt.hour)["기온차(서울-양평)"]
    .mean()
    .rename_axis("시각")
)
st.bar_chart(hourly_diff, x_label="시각 (시)", y_label="평균 기온차 (°C)")

st.divider()

# ── ③ 월별 평균 기온차 (막대그래프) ───────────────────────
st.header("③ 월(1~12월)별 평균 기온차 (서울 − 양평)")

monthly_diff = (
    df.groupby(df["일시"].dt.month)["기온차(서울-양평)"]
    .mean()
    .rename_axis("월")
)
st.bar_chart(monthly_diff, x_label="월", y_label="평균 기온차 (°C)")

st.divider()
st.caption("데이터 출처: 기상청 시간별 기온 자료 (서울_기온.csv, 양평_기온.csv)")
