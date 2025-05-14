import streamlit as st
import pandas as pd
import folium
import json
from streamlit.components.v1 import html
from modules.load_data import load_data

st.title("🍊 감귤 재배 적합도 Choropleth 지도")

# 데이터 로딩
df_weather, df_sunshine = load_data()

# GeoJSON 파일 로드
with open('data/jeju_geo.json', 'r', encoding='utf-8') as f:
    jeju_geo = json.load(f)

# 데이터 전처리
df_weather['연월'] = df_weather['일시'].dt.to_period('M').astype(str)
df_sunshine['연월'] = df_sunshine['일시'].dt.to_period('M').astype(str)

selected_month = st.selectbox("📅 기준 월 선택", sorted(df_weather['연월'].unique()), index=len(df_weather['연월'].unique())-1)

# 감귤 적합도 계산
df_merge = pd.merge(
    df_weather[df_weather['연월'] == selected_month],
    df_sunshine[df_sunshine['연월'] == selected_month],
    on=['지점명', '연월'],
    how='left'
)

df_merge['적합도점수'] = 0
df_merge['적합도점수'] += df_merge['평균기온(°C)'].apply(lambda x: 33 if 12 <= x <= 18 else 0)
df_merge['적합도점수'] += df_merge['평균상대습도(%)'].apply(lambda x: 33 if 60 <= x <= 85 else 0)
df_merge['적합도점수'] += df_merge['일조시간'].apply(lambda x: 34 if x >= 180 else 0)

# 지도 생성
m = folium.Map(location=[33.4, 126.5], zoom_start=9)

# Choropleth 레이어 추가
folium.Choropleth(
    geo_data=jeju_geo,
    data=df_merge,
    columns=['지점명', '적합도점수'],
    key_on='feature.properties.name',  # GeoJSON 파일의 지역명 필드
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='감귤 재배 적합도 점수 (%)'
).add_to(m)

# 팝업 마커 (선택사항)
for _, row in df_merge.iterrows():
    folium.Marker(
        location=[row['위도'], row['경도']],
        popup=f"{row['지점명']}<br>적합도: {row['적합도점수']}%",
        icon=folium.Icon(color='green' if row['적합도점수'] >= 66 else 'orange' if row['적합도점수'] >= 33 else 'gray')
    ).add_to(m)

# 지도 출력
html(m._repr_html_(), height=600, width=900)
