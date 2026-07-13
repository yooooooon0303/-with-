import streamlit as st
import pandas as pd

st.set_page_config(page_title="열섬현상과 전력수요 분석", layout="wide")

st.title("🌡️ 도시 열섬현상과 전력수요 분석")
st.caption("2025년 시간별 데이터 — 서울·양평 기온, 전력수요")


@st.cache_data
def load_temperature():
    seoul = pd.read_csv("서울_기온.csv", encoding="cp949")
    yangpyeong = pd.read_csv("양평_기온.csv", encoding="cp949")

    def preprocess(df, region_name):
        # '기온'이 포함된 열을 자동 탐색 (cp949 인코딩 시 °C 표기가 달라질 수 있음)
        temp_col = [c for c in df.columns if "기온" in c][0]
        df = df[["일시", temp_col]].rename(columns={temp_col: region_name})
        df["일시"] = pd.to_datetime(df["일시"])
        return df

    seoul = preprocess(seoul, "서울")
    yangpyeong = preprocess(yangpyeong, "양평")

    merged = pd.merge(seoul, yangpyeong, on="일시", how="inner")
    merged["기온차(서울-양평)"] = merged["서울"] - merged["양평"]
    return merged


@st.cache_data
def load_power():
    power = pd.read_csv("전력수요.csv", encoding="cp949")
    power_col = [c for c in power.columns if "전력" in c][0]
    power = power[["일시", power_col]].rename(columns={power_col: "전력수요(MWh)"})
    power["일시"] = pd.to_datetime(power["일시"])
    return power


temp_df = load_temperature()
power_df = load_power()

tab1, tab2 = st.tabs(["🏙️ 탭1: 열섬 분석", "⚡ 탭2: 전력 연결"])

# ═══════════════════ 탭1: 열섬 분석 ═══════════════════
with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("서울 연평균 기온", f"{temp_df['서울'].mean():.1f} °C")
    col2.metric("양평 연평균 기온", f"{temp_df['양평'].mean():.1f} °C")
    col3.metric("연평균 기온차 (서울-양평)", f"{temp_df['기온차(서울-양평)'].mean():.2f} °C")

    st.divider()

    # ① 1년간 기온 변화 (선그래프)
    st.header("① 1년간 두 지역의 기온 변화")
    view_option = st.radio(
        "표시 방식 선택",
        ["일평균 (보기 편함)", "시간별 원자료 (8,760개)"],
        horizontal=True,
    )
    if view_option.startswith("일평균"):
        chart_df = temp_df.set_index("일시")[["서울", "양평"]].resample("D").mean()
    else:
        chart_df = temp_df.set_index("일시")[["서울", "양평"]]
    st.line_chart(chart_df, x_label="일시", y_label="기온 (°C)")

    st.divider()

    # ② 시각별 평균 기온차 (막대그래프)
    st.header("② 시각(0~23시)별 평균 기온차 (서울 − 양평)")
    st.caption("열섬현상은 보통 밤~새벽 시간대에 기온차가 크게 나타납니다.")
    hourly_diff = (
        temp_df.groupby(temp_df["일시"].dt.hour)["기온차(서울-양평)"]
        .mean()
        .rename_axis("시각")
    )
    st.bar_chart(hourly_diff, x_label="시각 (시)", y_label="평균 기온차 (°C)")

    st.divider()

    # ③ 월별 평균 기온차 (막대그래프)
    st.header("③ 월(1~12월)별 평균 기온차 (서울 − 양평)")
    monthly_diff = (
        temp_df.groupby(temp_df["일시"].dt.month)["기온차(서울-양평)"]
        .mean()
        .rename_axis("월")
    )
    st.bar_chart(monthly_diff, x_label="월", y_label="평균 기온차 (°C)")

# ═══════════════════ 탭2: 전력 연결 ═══════════════════
with tab2:
    # 서울 기온 + 전력수요 병합
    seoul_power = pd.merge(
        temp_df[["일시", "서울"]].rename(columns={"서울": "기온(°C)"}),
        power_df,
        on="일시",
        how="inner",
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("연평균 전력수요", f"{seoul_power['전력수요(MWh)'].mean():,.0f} MWh")
    col2.metric("최대 전력수요", f"{seoul_power['전력수요(MWh)'].max():,.0f} MWh")
    corr = seoul_power["기온(°C)"].corr(seoul_power["전력수요(MWh)"])
    col3.metric("기온-전력수요 상관계수", f"{corr:.3f}")

    st.divider()

    # ① 기온 vs 전력수요 산점도
    st.header("① 기온과 전력수요의 산점도")
    st.caption("냉방·난방 수요 때문에 보통 U자형(양쪽 끝에서 전력수요 증가) 패턴이 나타납니다.")
    st.scatter_chart(
        seoul_power,
        x="기온(°C)",
        y="전력수요(MWh)",
        size=10,
    )

    st.divider()

    # ② 기온 구간별 평균 전력수요 (막대그래프)
    st.header("② 기온 구간별 평균 전력수요")
    t_min = int(seoul_power["기온(°C)"].min() // 5 * 5)
    t_max = int(seoul_power["기온(°C)"].max() // 5 * 5 + 5)
    bins = list(range(t_min, t_max + 1, 5))
    labels = [f"{b}~{b+5}°C" for b in bins[:-1]]
    seoul_power["기온구간"] = pd.cut(seoul_power["기온(°C)"], bins=bins, labels=labels)
    bin_mean = (
        seoul_power.groupby("기온구간", observed=True)["전력수요(MWh)"]
        .mean()
        .rename_axis("기온 구간")
    )
    st.bar_chart(bin_mean, x_label="기온 구간", y_label="평균 전력수요 (MWh)")

    st.divider()

    # ③ 월별 평균 전력수요 (막대그래프)
    st.header("③ 월(1~12월)별 평균 전력수요")
    monthly_power = (
        seoul_power.groupby(seoul_power["일시"].dt.month)["전력수요(MWh)"]
        .mean()
        .rename_axis("월")
    )
    st.bar_chart(monthly_power, x_label="월", y_label="평균 전력수요 (MWh)")

st.divider()
st.caption("데이터 출처: 기상청 시간별 기온 자료, 전력수요 자료 (서울_기온.csv, 양평_기온.csv, 전력수요.csv)")
