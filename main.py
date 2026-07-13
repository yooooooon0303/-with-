<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>기온과 대기오염 상관관계 분석</title>

    <!-- 그래프 제작 -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>

    <!-- CSV 파일 읽기 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js"></script>

    <!-- XLS 파일 읽기 -->
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, "Noto Sans KR", sans-serif;
            background: #f5f7fa;
            color: #1f2937;
        }

        main {
            width: min(1100px, 94%);
            margin: 28px auto 60px;
        }

        h1 {
            margin-bottom: 8px;
        }

        h2 {
            margin-top: 0;
            font-size: 1.15rem;
        }

        .subtitle {
            color: #4b5563;
            margin-top: 0;
        }

        .card {
            background: white;
            border-radius: 14px;
            padding: 20px;
            margin-top: 18px;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.07);
        }

        .question {
            font-weight: 700;
            line-height: 1.7;
        }

        .controls {
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }

        select {
            padding: 9px 12px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            font-size: 1rem;
            background: white;
        }

        .result-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-top: 16px;
        }

        .result-box {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 14px;
        }

        .result-box strong {
            display: block;
            font-size: 1.35rem;
            margin-top: 5px;
        }

        .conclusion {
            margin-top: 16px;
            padding: 14px;
            border-left: 5px solid #475569;
            background: #f8fafc;
            line-height: 1.75;
        }

        .chart-wrap {
            position: relative;
            height: 430px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }

        th,
        td {
            border-bottom: 1px solid #e5e7eb;
            padding: 10px;
            text-align: center;
        }

        th {
            background: #f8fafc;
        }

        .error {
            color: #b91c1c;
            font-weight: 700;
            white-space: pre-line;
        }

        .note {
            color: #64748b;
            font-size: 0.92rem;
            line-height: 1.65;
        }

        @media (max-width: 640px) {
            .chart-wrap {
                height: 360px;
            }
        }
    </style>
</head>

<body>
<main>

    <h1>기온과 대기오염물질 농도의 상관관계 분석</h1>

    <p class="subtitle">
        2025년 7~8월 서울 최고기온과 동작구 일평균 대기오염 자료 분석
    </p>

    <section class="card">
        <h2>탐구 질문</h2>

        <p class="question">
            2025년 7~8월 서울의 일 최고기온과 동작구의 일평균
            대기오염물질 농도 사이에는 어떤 상관관계가 나타나며,
            어떤 오염물질에서 그 관계가 가장 뚜렷한가?
        </p>
    </section>

    <section class="card">

        <div class="controls">
            <label for="pollutant">
                <strong>분석할 오염물질:</strong>
            </label>

            <select id="pollutant">
                <option value="PM2.5" selected>PM2.5</option>
                <option value="PM10">PM10</option>
                <option value="오존">오존</option>
                <option value="이산화질소">이산화질소</option>
                <option value="일산화탄소">일산화탄소</option>
                <option value="아황산가스">아황산가스</option>
            </select>
        </div>

        <div class="result-grid">

            <div class="result-box">
                분석 일수
                <strong id="count">-</strong>
            </div>

            <div class="result-box">
                피어슨 상관계수 r
                <strong id="correlation">-</strong>
            </div>

            <div class="result-box">
                결정계수 R²
                <strong id="rSquared">-</strong>
            </div>

        </div>

        <div id="conclusion" class="conclusion">
            자료를 불러오는 중입니다.
        </div>

        <p id="error" class="error"></p>

    </section>

    <section class="card">
        <h2>날짜별 최고기온과 오염물질 농도</h2>

        <div class="chart-wrap">
            <canvas id="timeChart"></canvas>
        </div>
    </section>

    <section class="card">
        <h2>최고기온과 오염물질 농도의 산점도</h2>

        <div class="chart-wrap">
            <canvas id="scatterChart"></canvas>
        </div>
    </section>

    <section class="card">
        <h2>오염물질별 상관계수 비교</h2>

        <table>
            <thead>
            <tr>
                <th>순위</th>
                <th>오염물질</th>
                <th>상관계수 r</th>
                <th>관계 해석</th>
            </tr>
            </thead>

            <tbody id="correlationTable"></tbody>
        </table>

        <p class="note">
            상관계수는 두 변수가 함께 변하는 정도를 나타내며,
            인과관계를 직접 증명하지는 않습니다.
            강수량, 풍속, 습도, 대기 정체, 오염물질 배출량 등
            다른 요인도 농도에 영향을 줄 수 있습니다.
        </p>
    </section>

</main>

<script>
    /*
     * 같은 폴더에 아래 세 데이터 파일을 넣어야 합니다.
     *
     * OBS_ASOS_DD_20260713131504.csv
     * 확정자료엑셀다운.xls
     * 확정자료엑셀다운 (1).xls
     */

    const TEMPERATURE_FILE =
        "OBS_ASOS_DD_20260713131504.csv";

    const AIR_FILES = [
        "확정자료엑셀다운.xls",
        "확정자료엑셀다운 (1).xls"
    ];

    const POLLUTANTS = {
        "PM2.5": {
            unit: "㎍/㎥"
        },

        "PM10": {
            unit: "㎍/㎥"
        },

        "오존": {
            unit: "ppm"
        },

        "이산화질소": {
            unit: "ppm"
        },

        "일산화탄소": {
            unit: "ppm"
        },

        "아황산가스": {
            unit: "ppm"
        }
    };

    let mergedData = [];

    let timeChart = null;
    let scatterChart = null;


    /*
     * 문자열 형태의 숫자를 실제 숫자로 변환합니다.
     */
    function toNumber(value) {
        if (
            value === null ||
            value === undefined ||
            value === ""
        ) {
            return NaN;
        }

        return Number(
            String(value)
                .replaceAll(",", "")
                .trim()
        );
    }


    /*
     * 최고기온 CSV 파일을 읽습니다.
     */
    async function readTemperatureCsv() {
        const response = await fetch(TEMPERATURE_FILE);

        if (!response.ok) {
            throw new Error(
                `${TEMPERATURE_FILE} 파일을 찾지 못했습니다.`
            );
        }

        const buffer = await response.arrayBuffer();

        /*
         * 기상청 CSV 파일은 CP949 계열이므로
         * euc-kr 방식으로 읽습니다.
         */
        const text =
            new TextDecoder("euc-kr").decode(buffer);

        const parsed = Papa.parse(text, {
            header: true,
            skipEmptyLines: true,

            transformHeader: function (header) {
                return header
                    .replace(/^\uFEFF/, "")
                    .trim();
            }
        });

        return parsed.data
            .map(function (row) {
                return {
                    date:
                        String(row["일시"] ?? "")
                            .trim()
                            .slice(0, 10),

                    temperature:
                        toNumber(row["최고기온(°C)"])
                };
            })
            .filter(function (row) {
                return (
                    row.date &&
                    Number.isFinite(row.temperature)
                );
            });
    }


    /*
     * 대기오염 XLS 파일을 읽습니다.
     */
    async function readAirExcel(fileName) {
        const response = await fetch(fileName);

        if (!response.ok) {
            throw new Error(
                `${fileName} 파일을 찾지 못했습니다.`
            );
        }

        const buffer = await response.arrayBuffer();

        const workbook = XLSX.read(buffer, {
            type: "array"
        });

        const firstSheet =
            workbook.Sheets[workbook.SheetNames[0]];

        return XLSX.utils.sheet_to_json(
            firstSheet,
            {
                defval: null
            }
        );
    }


    /*
     * 시간별 대기오염 자료를
     * 날짜별 평균 농도로 변환합니다.
     */
    function makeDailyAirAverage(rows) {
        const grouped = new Map();

        for (const row of rows) {
            const date =
                String(row["날짜"] ?? "")
                    .trim()
                    .slice(0, 10);

            if (!date) {
                continue;
            }

            if (!grouped.has(date)) {
                const initial = {};

                for (
                    const pollutant
                    of Object.keys(POLLUTANTS)
                ) {
                    initial[pollutant] = {
                        sum: 0,
                        count: 0
                    };
                }

                grouped.set(date, initial);
            }

            const day = grouped.get(date);

            for (
                const pollutant
                of Object.keys(POLLUTANTS)
            ) {
                const value =
                    toNumber(row[pollutant]);

                /*
                 * 음수나 비정상 값은 평균 계산에서 제외합니다.
                 */
                if (
                    Number.isFinite(value) &&
                    value >= 0
                ) {
                    day[pollutant].sum += value;
                    day[pollutant].count += 1;
                }
            }
        }

        const result = new Map();

        for (
            const [date, day]
            of grouped.entries()
        ) {
            const averages = {};

            for (
                const pollutant
                of Object.keys(POLLUTANTS)
            ) {
                const item = day[pollutant];

                averages[pollutant] =
                    item.count > 0
                        ? item.sum / item.count
                        : NaN;
            }

            result.set(date, averages);
        }

        return result;
    }


    /*
     * 피어슨 상관계수 계산
     */
    function pearson(x, y) {
        const n = x.length;

        if (n < 2) {
            return NaN;
        }

        const meanX =
            x.reduce(
                (sum, value) => sum + value,
                0
            ) / n;

        const meanY =
            y.reduce(
                (sum, value) => sum + value,
                0
            ) / n;

        let numerator = 0;
        let sumX2 = 0;
        let sumY2 = 0;

        for (let i = 0; i < n; i++) {
            const dx = x[i] - meanX;
            const dy = y[i] - meanY;

            numerator += dx * dy;
            sumX2 += dx * dx;
            sumY2 += dy * dy;
        }

        const denominator =
            Math.sqrt(sumX2 * sumY2);

        if (denominator === 0) {
            return NaN;
        }

        return numerator / denominator;
    }


    /*
     * 선형 회귀식 계산
     *
     * y = slope × x + intercept
     */
    function linearRegression(x, y) {
        const n = x.length;

        const meanX =
            x.reduce(
                (sum, value) => sum + value,
                0
            ) / n;

        const meanY =
            y.reduce(
                (sum, value) => sum + value,
                0
            ) / n;

        let numerator = 0;
        let denominator = 0;

        for (let i = 0; i < n; i++) {
            numerator +=
                (x[i] - meanX) *
                (y[i] - meanY);

            denominator +=
                (x[i] - meanX) ** 2;
        }

        const slope =
            denominator === 0
                ? 0
                : numerator / denominator;

        const intercept =
            meanY - slope * meanX;

        return {
            slope: slope,
            intercept: intercept
        };
    }


    /*
     * 상관관계의 방향과 강도를 설명합니다.
     */
    function relationText(r) {
        const strength = Math.abs(r);

        let level;

        if (strength >= 0.7) {
            level = "강한";
        } else if (strength >= 0.4) {
            level = "중간 정도의";
        } else if (strength >= 0.2) {
            level = "약한";
        } else {
            level = "매우 약한";
        }

        let direction;

        if (r > 0) {
            direction = "양의";
        } else if (r < 0) {
            direction = "음의";
        } else {
            direction = "거의 없는";
        }

        return `${level} ${direction} 상관관계`;
    }


    /*
     * 선택한 오염물질의 유효한 데이터만 가져옵니다.
     */
    function validRowsFor(pollutant) {
        return mergedData.filter(function (row) {
            return (
                Number.isFinite(row.temperature) &&
                Number.isFinite(row[pollutant])
            );
        });
    }


    /*
     * 선택한 오염물질에 따라 결과와 그래프를 갱신합니다.
     */
    function updateSummaryAndCharts() {
        const pollutant =
            document.getElementById("pollutant").value;

        const unit =
            POLLUTANTS[pollutant].unit;

        const rows =
            validRowsFor(pollutant);

        if (rows.length < 2) {
            document.getElementById("conclusion")
                .textContent =
                "분석할 수 있는 자료가 부족합니다.";

            return;
        }

        const temperatures =
            rows.map(row => row.temperature);

        const pollutionValues =
            rows.map(row => row[pollutant]);

        const r =
            pearson(
                temperatures,
                pollutionValues
            );

        const rSquared = r ** 2;

        const regression =
            linearRegression(
                temperatures,
                pollutionValues
            );

        document.getElementById("count")
            .textContent =
            `${rows.length}일`;

        document.getElementById("correlation")
            .textContent =
            Number.isFinite(r)
                ? r.toFixed(3)
                : "계산 불가";

        document.getElementById("rSquared")
            .textContent =
            Number.isFinite(rSquared)
                ? rSquared.toFixed(3)
                : "계산 불가";


        let directionSentence;

        if (r > 0) {
            directionSentence =
                "최고기온이 높은 날일수록 농도가 높아지는 경향이 나타났다";
        } else if (r < 0) {
            directionSentence =
                "최고기온이 높은 날일수록 농도가 낮아지는 경향이 나타났다";
        } else {
            directionSentence =
                "최고기온과 농도 사이에 뚜렷한 방향성이 나타나지 않았다";
        }

        document.getElementById("conclusion")
            .innerHTML =
            `<strong>자동 분석:</strong> ` +
            `${pollutant}의 피어슨 상관계수는 ` +
            `<strong>r = ${r.toFixed(3)}</strong>으로, ` +
            `<strong>${relationText(r)}</strong>가 나타났다. ` +
            `따라서 이 자료에서는 ${directionSentence}. ` +
            `다만 이 결과만으로 기온이 ${pollutant} 농도를 ` +
            `직접 변화시켰다고 단정할 수는 없다.`;


        /*
         * 기존 그래프가 있으면 삭제하고 다시 생성합니다.
         */
        if (timeChart) {
            timeChart.destroy();
        }

        if (scatterChart) {
            scatterChart.destroy();
        }


        /*
         * 날짜별 최고기온과 오염물질 농도 비교 그래프
         */
        timeChart =
            new Chart(
                document.getElementById("timeChart"),
                {
                    type: "bar",

                    data: {
                        labels:
                            rows.map(row => row.date),

                        datasets: [
                            {
                                label: "최고기온(°C)",
                                data: temperatures,
                                type: "line",
                                yAxisID: "temperatureAxis",
                                tension: 0.2,
                                pointRadius: 2
                            },
                            {
                                label:
                                    `${pollutant} 일평균(${unit})`,
                                data: pollutionValues,
                                type: "bar",
                                yAxisID: "pollutionAxis"
                            }
                        ]
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false,

                        interaction: {
                            mode: "index",
                            intersect: false
                        },

                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: "날짜"
                                },

                                ticks: {
                                    maxRotation: 0,
                                    autoSkip: true,
                                    maxTicksLimit: 12
                                }
                            },

                            temperatureAxis: {
                                position: "left",

                                title: {
                                    display: true,
                                    text: "최고기온(°C)"
                                }
                            },

                            pollutionAxis: {
                                position: "right",

                                title: {
                                    display: true,
                                    text:
                                        `${pollutant}(${unit})`
                                },

                                grid: {
                                    drawOnChartArea: false
                                }
                            }
                        }
                    }
                }
            );


        /*
         * 회귀 추세선의 양 끝점 계산
         */
        const minimumTemperature =
            Math.min(...temperatures);

        const maximumTemperature =
            Math.max(...temperatures);

        const regressionLine = [
            {
                x: minimumTemperature,

                y:
                    regression.slope *
                    minimumTemperature +
                    regression.intercept
            },

            {
                x: maximumTemperature,

                y:
                    regression.slope *
                    maximumTemperature +
                    regression.intercept
            }
        ];


        /*
         * 최고기온과 오염물질 농도의 산점도
         */
        scatterChart =
            new Chart(
                document.getElementById("scatterChart"),
                {
                    type: "scatter",

                    data: {
                        datasets: [
                            {
                                label:
                                    `${pollutant} 관측값`,

                                data:
                                    rows.map(function (row) {
                                        return {
                                            x: row.temperature,
                                            y: row[pollutant],
                                            date: row.date
                                        };
                                    }),

                                pointRadius: 5
                            },

                            {
                                label:
                                    "선형 회귀 추세선",

                                type: "line",
                                data: regressionLine,
                                pointRadius: 0,
                                borderWidth: 2
                            }
                        ]
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false,

                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label:
                                        function (context) {
                                            const point =
                                                context.raw;

                                            if (!point.date) {
                                                return (
                                                    "추세선: " +
                                                    point.y.toFixed(3)
                                                );
                                            }

                                            return (
                                                `${point.date}: ` +
                                                `${point.x}°C, ` +
                                                `${point.y.toFixed(3)} ${unit}`
                                            );
                                        }
                                }
                            }
                        },

                        scales: {
                            x: {
                                type: "linear",

                                title: {
                                    display: true,
                                    text: "일 최고기온(°C)"
                                }
                            },

                            y: {
                                title: {
                                    display: true,
                                    text:
                                        `${pollutant} 일평균 농도(${unit})`
                                }
                            }
                        }
                    }
                }
            );
    }


    /*
     * 오염물질별 상관계수를 계산하여 순위를 표시합니다.
     */
    function renderCorrelationTable() {
        const ranking =
            Object.keys(POLLUTANTS)
                .map(function (pollutant) {
                    const rows =
                        validRowsFor(pollutant);

                    const r =
                        pearson(
                            rows.map(
                                row => row.temperature
                            ),

                            rows.map(
                                row => row[pollutant]
                            )
                        );

                    return {
                        pollutant: pollutant,
                        r: r
                    };
                })

                /*
                 * 상관계수 절댓값이 큰 순서대로 정렬
                 */
                .sort(function (a, b) {
                    return (
                        Math.abs(b.r) -
                        Math.abs(a.r)
                    );
                });

        document.getElementById(
            "correlationTable"
        ).innerHTML =
            ranking
                .map(function (item, index) {
                    return `
                        <tr>
                            <td>${index + 1}</td>
                            <td>${item.pollutant}</td>
                            <td>${item.r.toFixed(3)}</td>
                            <td>${relationText(item.r)}</td>
                        </tr>
                    `;
                })
                .join("");
    }


    /*
     * 모든 자료를 불러오고 날짜를 기준으로 병합합니다.
     */
    async function loadData() {
        try {
            const [
                temperatureRows,
                ...airFileRows
            ] =
                await Promise.all([
                    readTemperatureCsv(),

                    ...AIR_FILES.map(
                        readAirExcel
                    )
                ]);

            /*
             * 7월과 8월 대기오염 자료를 하나로 합칩니다.
             */
            const allAirRows =
                airFileRows.flat();

            /*
             * 시간별 자료를 일평균으로 변환합니다.
             */
            const dailyAir =
                makeDailyAirAverage(
                    allAirRows
                );

            /*
             * 기온 자료와 대기오염 자료를
             * 날짜를 기준으로 병합합니다.
             */
            mergedData =
                temperatureRows
                    .filter(function (row) {
                        return dailyAir.has(row.date);
                    })

                    .map(function (row) {
                        return {
                            date: row.date,
                            temperature:
                                row.temperature,

                            ...dailyAir.get(row.date)
                        };
                    })

                    .sort(function (a, b) {
                        return a.date.localeCompare(b.date);
                    });

            if (mergedData.length < 2) {
                throw new Error(
                    "날짜가 일치하는 자료가 부족합니다. " +
                    "파일의 날짜 범위를 확인하세요."
                );
            }

            renderCorrelationTable();
            updateSummaryAndCharts();

            document
                .getElementById("pollutant")
                .addEventListener(
                    "change",
                    updateSummaryAndCharts
                );

        } catch (error) {
            console.error(error);

            document.getElementById("error")
                .textContent =
                `오류: ${error.message}\n` +
                `HTML 파일을 더블클릭하지 말고 ` +
                `GitHub Pages 또는 로컬 서버에서 실행하세요.`;

            document.getElementById("conclusion")
                .textContent =
                "자료를 불러오지 못했습니다.";
        }
    }

    loadData();
</script>

</body>
</html>
