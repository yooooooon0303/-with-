from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="기온과 대기오염 상관관계 분석",
    page_icon="🌡️",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent

TEMP_FILE = BASE_DIR / "OBS_ASOS_DD_20260713131504.csv"

AIR_FILES = [
    BASE_DIR / "확정자료엑셀다운.xls",
    BASE_DIR / "확정자료엑셀다운 (1).xls",
]

POLLUTANT_UNITS = {
    "PM2.5": "㎍/㎥",
    "PM10": "㎍/㎥",
    "오존": "ppm",
    "이산화질소": "ppm",
    "일산화탄소": "ppm",
    "아황산가스": "ppm",
}


# -----------------------------
# 데이터 불러오기
# -----------------------------
@st.cache_data
def load_temperature(file_path: str) -> pd.DataFrame:
    """기상청 CSV에서 날짜와 최고기온을 불러온다."""

    data = None
    last_error = None

    for encoding in ("cp949", "euc-kr", "utf-8-sig", "utf-8"):
        try:
            data = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError as error:
            last_error = error

    if data is None:
        raise ValueError(
            "기온 CSV 파일의 문자 인코딩을 읽지 못했습니다."
        ) from last_error

    required_columns = {"일시", "최고기온(°C)"}
    missing = required_columns - set(data.columns)

    if missing:
        raise ValueError(
            f"기온 파일에 필요한 열이 없습니다: {sorted(missing)}"
        )

    result = data[["일시", "최고기온(°C)"]].copy()
    result.columns = ["날짜", "최고기온"]

    result["날짜"] = pd.to_datetime(
        result["날짜"],
        errors="coerce",
    )

    result["최고기온"] = pd.to_numeric(
        result["최고기온"],
        errors="coerce",
    )

    return (
        result
        .dropna(subset=["날짜", "최고기온"])
        .drop_duplicates(subset="날짜")
        .sort_values("날짜")
    )


@st.cache_data
def load_air_quality(
    file_paths: tuple[str, ...]
) -> pd.DataFrame:
    """시간별 XLS 자료를 합쳐 날짜별 평균 농도로 변환한다."""

    frames = [
        pd.read_excel(file_path, engine="xlrd")
        for file_path in file_paths
    ]

    data = pd.concat(
        frames,
        ignore_index=True,
    )

    required_columns = {
        "날짜",
        *POLLUTANT_UNITS.keys(),
    }

    missing = required_columns - set(data.columns)

    if missing:
        raise ValueError(
            f"대기오염 파일에 필요한 열이 없습니다: {sorted(missing)}"
        )

    # '2025-07-01 01'에서 날짜 부분만 추출
    data["날짜"] = pd.to_datetime(
        data["날짜"]
        .astype(str)
        .str.slice(0, 10),
        errors="coerce",
    )

    for pollutant in POLLUTANT_UNITS:
        data[pollutant] = pd.to_numeric(
            data[pollutant],
            errors="coerce",
        )

        # 음수인 비정상 측정값 제거
        data.loc[
            data[pollutant] < 0,
            pollutant
        ] = np.nan

    # 시간별 측정값을 날짜별 평균으로 변환
    daily_average = (
        data
        .dropna(subset=["날짜"])
        .groupby(
            "날짜",
            as_index=False,
        )[list(POLLUTANT_UNITS)]
        .mean(numeric_only=True)
        .sort_values("날짜")
    )

    return daily_average


# -----------------------------
# 상관관계 해석 함수
# -----------------------------
def describe_correlation(r: float) -> str:
    strength = abs(r)

    if strength >= 0.7:
        level = "강한"
    elif strength >= 0.4:
        level = "중간 정도의"
    elif strength >= 0.2:
        level = "약한"
    else:
        level = "매우 약한"

    if r > 0:
        direction = "양의"
    elif r < 0:
        direction = "음의"
    else:
        direction = "거의 없는"

    return f"{level} {direction} 상관관계"


# -----------------------------
# 날짜별 비교 그래프
# -----------------------------
def make_time_chart(
    data: pd.DataFrame,
    pollutant: str,
) -> go.Figure:

    unit = POLLUTANT_UNITS[pollutant]

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=data["날짜"],
            y=data["최고기온"],
            mode="lines+markers",
            name="최고기온(°C)",
            yaxis="y",
        )
    )

    figure.add_trace(
        go.Bar(
            x=data["날짜"],
            y=data[pollutant],
            name=f"{pollutant} 일평균({unit})",
            yaxis="y2",
            opacity=0.55,
        )
    )

    figure.update_layout(
        title=f"날짜별 최고기온과 {pollutant} 농도",
        xaxis_title="날짜",

        yaxis=dict(
            title="최고기온(°C)",
        ),

        yaxis2=dict(
            title=f"{pollutant}({unit})",
            overlaying="y",
            side="right",
            showgrid=False,
        ),

        hovermode="x unified",

        legend=dict(
            orientation="h",
            y=1.12,
        ),

        margin=dict(
            l=40,
            r=40,
            t=85,
            b=40,
        ),
    )

    return figure


# -----------------------------
# 산점도와 회귀선
# -----------------------------
def make_scatter_chart(
    data: pd.DataFrame,
    pollutant: str,
) -> tuple[go.Figure, float, float]:

    unit = POLLUTANT_UNITS[pollutant]

    x = data["최고기온"].to_numpy(dtype=float)
    y = data[pollutant].to_numpy(dtype=float)

    # 1차 선형회귀
    slope, intercept = np.polyfit(
        x,
        y,
        1,
    )

    line_x = np.linspace(
        x.min(),
        x.max(),
        100,
    )

    line_y = slope * line_x + intercept

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            name="관측값",

            customdata=data["날짜"].dt.strftime(
                "%Y-%m-%d"
            ),

            hovertemplate=(
                "날짜: %{customdata}<br>"
                "최고기온: %{x:.1f}°C<br>"
                f"{pollutant}: "
                + "%{y:.3f} "
                + unit
                + "<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=line_x,
            y=line_y,
            mode="lines",
            name="선형 회귀선",
            hoverinfo="skip",
        )
    )

    figure.update_layout(
        title=f"최고기온과 {pollutant}의 관계",
        xaxis_title="일 최고기온(°C)",
        yaxis_title=f"{pollutant} 일평균 농도({unit})",

        legend=dict(
            orientation="h",
            y=1.12,
        ),

        margin=dict(
            l=40,
            r=30,
            t=85,
            b=40,
        ),
    )

    return (
        figure,
        float(slope),
        float(intercept),
    )


# -----------------------------
# 웹앱 화면
# -----------------------------
st.title(
    "🌡️ 기온과 대기오염물질 농도의 상관관계 분석"
)

st.caption(
    "2025년 7~8월 서울 최고기온과 "
    "동작구 일평균 대기오염 자료"
)

st.info(
    "**탐구 질문:** 2025년 7~8월 서울의 일 최고기온과 "
    "동작구의 일평균 대기오염물질 농도 사이에는 "
    "어떤 상관관계가 나타나며, 어떤 오염물질에서 "
    "그 관계가 가장 뚜렷한가?"
)


# -----------------------------
# 파일 존재 확인
# -----------------------------
all_files = [
    TEMP_FILE,
    *AIR_FILES,
]

missing_files = [
    file.name
    for file in all_files
    if not file.exists()
]

if missing_files:
    st.error(
        "다음 파일이 main.py와 같은 폴더에 없습니다:\n- "
        + "\n- ".join(missing_files)
    )

    st.stop()


# -----------------------------
# 데이터 결합
# -----------------------------
try:
    temperature_data = load_temperature(
        str(TEMP_FILE)
    )

    air_data = load_air_quality(
        tuple(
            str(file)
            for file in AIR_FILES
        )
    )

except Exception as error:
    st.error(
        f"데이터를 불러오는 중 오류가 발생했습니다: {error}"
    )

    st.stop()


merged = temperature_data.merge(
    air_data,
    on="날짜",
    how="inner",
)

if len(merged) < 2:
    st.error(
        "기온 자료와 대기오염 자료에서 "
        "날짜가 일치하는 값이 2개 미만입니다."
    )

    st.stop()


# -----------------------------
# 오염물질 선택
# -----------------------------
pollutant = st.selectbox(
    "분석할 오염물질을 선택하세요.",
    options=list(POLLUTANT_UNITS),
    index=0,
)

analysis_data = merged[
    [
        "날짜",
        "최고기온",
        pollutant,
    ]
].dropna().copy()

if (
    len(analysis_data) < 2
    or analysis_data["최고기온"].nunique() < 2
):
    st.error(
        "상관관계와 회귀선을 계산하기에 "
        "유효한 자료가 부족합니다."
    )

    st.stop()


# -----------------------------
# 상관계수와 결정계수
# -----------------------------
correlation = float(
    analysis_data["최고기온"].corr(
        analysis_data[pollutant]
    )
)

r_squared = correlation ** 2


metric_1, metric_2, metric_3 = st.columns(3)

metric_1.metric(
    "분석 일수",
    f"{len(analysis_data)}일",
)

metric_2.metric(
    "피어슨 상관계수 r",
    f"{correlation:.3f}",
)

metric_3.metric(
    "결정계수 R²",
    f"{r_squared:.3f}",
)


if correlation > 0:
    tendency = (
        "최고기온이 높은 날일수록 "
        "농도도 높아지는 경향"
    )

elif correlation < 0:
    tendency = (
        "최고기온이 높은 날일수록 "
        "농도는 낮아지는 경향"
    )

else:
    tendency = (
        "최고기온과 농도 사이에 "
        "뚜렷한 방향성이 없는 경향"
    )


st.success(
    f"**분석 결과:** {pollutant}의 피어슨 상관계수는 "
    f"**r = {correlation:.3f}**으로, "
    f"**{describe_correlation(correlation)}**가 나타났습니다. "
    f"이 자료에서는 {tendency}이 확인되었습니다. "
    "다만 상관관계만으로 기온이 오염물질 농도를 "
    "직접 변화시켰다고 단정할 수는 없습니다."
)


# -----------------------------
# 그래프 출력
# -----------------------------
left, right = st.columns(2)

with left:
    st.plotly_chart(
        make_time_chart(
            analysis_data,
            pollutant,
        )
    )

with right:
    scatter_chart, slope, intercept = (
        make_scatter_chart(
            analysis_data,
            pollutant,
        )
    )

    st.plotly_chart(
        scatter_chart
    )


st.caption(
    f"선형 회귀식: {pollutant} 농도 = "
    f"{slope:.4f} × 최고기온 + {intercept:.4f}"
)


# -----------------------------
# 오염물질별 상관관계 비교
# -----------------------------
ranking_rows = []

for item in POLLUTANT_UNITS:

    valid = merged[
        [
            "최고기온",
            item,
        ]
    ].dropna()

    if (
        len(valid) >= 2
        and valid["최고기온"].nunique() >= 2
    ):
        item_r = float(
            valid["최고기온"].corr(
                valid[item]
            )
        )

    else:
        item_r = np.nan

    ranking_rows.append(
        {
            "오염물질": item,
            "상관계수 r": item_r,

            "상관계수 절댓값": (
                abs(item_r)
                if pd.notna(item_r)
                else np.nan
            ),

            "관계 해석": (
                describe_correlation(item_r)
                if pd.notna(item_r)
                else "계산 불가"
            ),
        }
    )


ranking = (
    pd.DataFrame(ranking_rows)
    .sort_values(
        "상관계수 절댓값",
        ascending=False,
        na_position="last",
    )
    .reset_index(drop=True)
)

ranking.index = ranking.index + 1
ranking.index.name = "순위"


st.subheader(
    "오염물질별 상관관계 비교"
)

st.dataframe(
    ranking[
        [
            "오염물질",
            "상관계수 r",
            "관계 해석",
        ]
    ].style.format(
        {
            "상관계수 r": "{:.3f}",
        },
        na_rep="-",
    )
)


# -----------------------------
# 최종 결론
# -----------------------------
valid_ranking = ranking.dropna(
    subset=["상관계수 r"]
)

if not valid_ranking.empty:

    strongest = valid_ranking.iloc[0]

    st.write(
        "**최종 결론:** 분석한 오염물질 중 "
        "최고기온과의 상관관계가 가장 뚜렷한 물질은 "
        f"**{strongest['오염물질']}**이며, "
        "상관계수는 "
        f"**r = {strongest['상관계수 r']:.3f}**입니다. "
        "그러나 대기오염 농도는 강수량, 풍속, 습도, "
        "대기 정체, 오염물질 배출량 등 여러 요인의 "
        "영향을 받으므로, 이 결과는 두 변수 사이의 "
        "관련성을 보여주는 것이며 인과관계를 "
        "증명하지는 않습니다."
    )


# -----------------------------
# 분석 데이터 다운로드
# -----------------------------
st.download_button(
    label="병합된 분석 데이터 CSV 다운로드",

    data=merged.to_csv(
        index=False
    ).encode("utf-8-sig"),

    file_name=(
        "temperature_air_quality_merged.csv"
    ),

    mime="text/csv",
)
