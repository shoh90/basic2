import streamlit as st
import pandas as pd
import folium
from streamlit.components.v1 import html
from modules.load_data import load_data

# 타이틀
st.set_page_config(page_title="감귤 생산성 및 병해충 통합 지도", layout="wide")
st.title("🍊 감귤 생산성 및 병해충 통합 모니터링 (2025년 기준)")

# 데이터 불러오기
df_weather, df_sunshine, df_disease_4, df_disease_5 = load_data()

# 연월 컬럼 생성
df_weather['연월'] = df_weather['일시'].dt.to_period('M').astype(str)
df_sunshine['연월'] = df_sunshine['일시'].dt.to_period('M').astype(str)

# 월 선택
month_options = sorted(df_weather['연월'].unique())
selected_month = st.selectbox("📅 기준 월 선택", month_options, index=len(month_options)-1)

# 지점 좌표
stations = {
    '제주시': (33.4996, 126.5312),
    '고산': (33.2931, 126.1628),
    '서귀포': (33.2540, 126.5618),
    '성산': (33.3875, 126.8808),
    '고흥': (34.6076, 127.2871),
    '완도': (34.3111, 126.7531)
}

# 데이터 병합
df_selected = pd.merge(
    df_weather[df_weather['연월'] == selected_month],
    df_sunshine[df_sunshine['연월'] == selected_month],
    on=['지점명', '연월'],
    how='left'
)

# 병해충 데이터 병합
df_disease_4 = df_disease_4[df_disease_4['연월'] == selected_month]
df_disease_5 = df_disease_5[df_disease_5['연월'] == selected_month]

df_selected = df_selected.merge(df_disease_4, on='지점명', how='left').merge(df_disease_5, on='지점명', how='left')

# 지도 초기화
fmap = folium.Map(location=[34.0, 126.5], zoom_start=8)

# 병해충 위험 기준 함수
def pest_risk(temp, humid):
    if temp >= 25 and humid >= 80:
        return "위험"
    elif temp >= 20 and humid >= 75:
        return "주의"
    else:
        return "양호"

# 마커 추가
for station, (lat, lon) in stations.items():
    row = df_selected[df_selected['지점명'] == station]
    if row.empty: continue

    row = row.iloc[0]
    temp = row['평균기온(°C)']
    humid = row['평균상대습도(%)']
    sunshine = row.get('일조시간', None)
    radiation = row.get('일사량', None)
    disease_4 = row.get('발생지수_병해충4', 'N/A')
    disease_5 = row.get('발생지수_병해충5', 'N/A')

    # 적합/부적합 기준
    suitable = (12 <= temp <= 18) and (60 <= humid <= 85) and (sunshine and sunshine >= 180)

    # 병해충 위험도
    pest_status = pest_risk(temp, humid)

    # 색상 (온도 기준 → 병해충 보조)
    if pest_status == "위험":
        color = 'red'
    elif pest_status == "주의":
        color = 'orange'
    else:
        color = 'green' if suitable else 'gray'

    # Tooltip
    tooltip = f"""
    <b>{station} ({selected_month})</b><br>
    🌡 평균기온: {temp:.1f}°C<br>
    💧 평균습도: {humid:.1f}%<br>
    ☀️ 일조시간: {sunshine if sunshine else '-'} h<br>
    🔆 일사량: {radiation if radiation else '-'} MJ/m²<br>
    🟢 재배 적합도: {'적합' if suitable else '부적합'}<br>
    🐛 병해충 위험도: <b>{pest_status}</b><br>
    🦠 병해충4 지수: {disease_4}<br>
    🦠 병해충5 지수: {disease_5}
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
html(fmap._repr_html_(), height=600, width=1000)
