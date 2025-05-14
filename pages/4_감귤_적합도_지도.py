import streamlit as st
import pandas as pd
import folium
from streamlit.components.v1 import html
from modules.load_data import load_data

st.title("🍊 감귤 재배 적합도 Choropleth 지도")

# 데이터 로딩
df_weather, df_sunshine = load_data()

# 지점 좌표 (딕셔너리 → DataFrame 변환)
stations = {
    '제주시': (33.4996, 126.5312),
    '고산': (33.2931, 126.1628),
    '서귀포': (33.2540, 126.5618),
    '성산': (33.3875, 126.8808),
    '고흥': (34.6076, 127.2871),
    '완도': (34.3111, 126.7531)
}
df_coords = pd.DataFrame.from_dict(stations, orient='index', columns=['위도', '경도']).reset_index().rename(columns={'index': '지점명'})

# 연월 컬럼 생성
df_weather['연월'] = df_weather['일시'].dt.to_period('M').astype(str)
df_sunshine['연월'] = df_sunshine['일시'].dt.to_period('M').astype(str)

# 기준 월 선택
selected_month = st.selectbox("📅 기준 월 선택", sorted(df_weather['연월'].unique()), index=len(df_weather['연월'].unique())-1)

# 데이터 병합
df_merge = pd.merge(
    df_weather[df_weather['연월'] == selected_month],
    df_sunshine[df_sunshine['연월'] == selected_month],
    on=['지점명', '연월'],
    how='left'
)
df_merge = pd.merge(df_merge, df_coords, on='지점명', how='left')

# 적합도 점수 계산
df_merge['적합도점수'] = 0
df_merge['적합도점수'] += df_merge['평균기온(°C)'].apply(lambda x: 33 if 12 <= x <= 18 else 0)
df_merge['적합도점수'] += df_merge['평균상대습도(%)'].apply(lambda x: 33 if 60 <= x <= 85 else 0)
df_merge['적합도점수'] += df_merge['합계 일조시간(hr)'].apply(lambda x: 34 if x >= 180 else 0)

# 지도 생성
m = folium.Map(location=[33.4, 126.5], zoom_start=9)

# Circle Marker 표시
for _, row in df_merge.iterrows():
    score = row['적합도점수']
    color = 'green' if score >= 66 else 'orange' if score >= 33 else 'gray'
    tooltip = f"{row['지점명']} ({selected_month})<br>적합도: {score}%"
    folium.CircleMarker(
        location=[row['위도'], row['경도']],
        radius=10,
        color=color,
        fill=True,
        fill_opacity=0.9,
        popup=tooltip
    ).add_to(m)

# 지도 출력
html(m._repr_html_(), height=600, width=900)
