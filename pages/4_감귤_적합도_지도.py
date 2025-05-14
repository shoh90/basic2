import streamlit as st
import pandas as pd
import folium
from streamlit.components.v1 import html
from modules.load_data import load_data

st.title("🍊 감귤 재배 적합도 & 병해충 위험 지도")

# 데이터 불러오기
df_weather, df_sunshine = load_data()

# 연월 컬럼 생성
df_weather['연월'] = df_weather['일시'].dt.to_period('M').astype(str)
df_sunshine['연월'] = df_sunshine['일시'].dt.to_period('M').astype(str)

# 월 선택
month_options = sorted(df_weather['연월'].unique())
selected_month = st.selectbox("월을 선택하세요", month_options, index=len(month_options)-1)

# 지점별 좌표
stations = {
    '제주시': (33.4996, 126.5312),
    '고산': (33.2931, 126.1628),
    '서귀포': (33.2540, 126.5618),
    '성산': (33.3875, 126.8808),
    '고흥': (34.6076, 127.2871),
    '완도': (34.3111, 126.7531)
}

# 데이터 병합 (weather + sunshine)
df_selected = pd.merge(
    df_weather[df_weather['연월'] == selected_month],
    df_sunshine[df_sunshine['연월'] == selected_month],
    on=['지점명', '연월'],
    how='left'
)

# 지도 초기화
fmap = folium.Map(location=[34.0, 126.5], zoom_start=8)

# 병해충 위험 기준 함수 (예시: 고온다습 위험도)
def pest_risk(temp, humid):
    if temp >= 25 and humid >= 80:
        return "위험"
    elif temp >= 20 and humid >= 75:
        return "주의"
    else:
        return "양호"

# 마커 추가
for station, (lat, lon) in stations.items():
    data = df_selected[df_selected['지점명'] == station]
    if data.empty: continue

    row = data.iloc[0]
    temp = row['평균기온(°C)']
    humid = row['평균상대습도(%)']
    sunshine = row.get('일조시간', None)
    radiation = row.get('일사량', None)

    # 감귤 재배 적합도 점수
    suitable_temp_humid = (12 <= temp <= 18) and (60 <= humid <= 85)
    score = 0
    score += 40 if suitable_temp_humid else 0
    score += 30 if sunshine and sunshine >= 150 else 0
    score += 30 if radiation and radiation >= 400 else 0

    # 병해충 위험도
    pest_status = pest_risk(temp, humid)

    # 색상 결정 (적합도+병해충)
    if pest_status == "위험":
        color = 'red'
    elif pest_status == "주의":
        color = 'orange'
    else:
        color = 'green' if score >= 70 else 'gray'

    # Tooltip 구성
    tooltip = f"""
    <b>{station} ({selected_month})</b><br>
    🌡 평균기온: {temp:.1f}°C<br>
    💧 평균습도: {humid:.1f}%<br>
    ☀️ 일조시간: {sunshine if sunshine else '-'} h<br>
    🔆 일사량: {radiation if radiation else '-'} MJ/m²<br>
    <b>적합도 점수: {score}%</b><br>
    🐛 병해충 위험도: <b>{pest_status}</b>
    """

    folium.CircleMarker(
        location=[lat, lon],
        radius=10,
        color=color,
        fill=True,
        fill_opacity=0.9,
        popup=folium.Popup(tooltip, max_width=300)
    ).add_to(fmap)

# 지도 출력
html(fmap._repr_html_(), height=550, width=750)
