import streamlit as st
import folium
import pandas as pd
import sqlite3
import json
from streamlit_folium import st_folium

# 🔶 설정
st.set_page_config(page_title="제주 감귤 재배 적합도", layout="wide")

# 🔶 db 경로 설정
db_path = "data/asos_weather.db"
geojson_path = "data/jeju_geo.json"

# 🔶 데이터 로딩 (jeju_geo.json)
with open(geojson_path, encoding='utf-8') as f:
    geo_data = json.load(f)

coord_dict = {f['properties']['name']: f['geometry']['coordinates'] for f in geo_data['features'] if f['properties']['name']}

# 🔶 DB 연결 및 데이터 불러오기
conn = sqlite3.connect(db_path)
query = "SELECT * FROM asos_weather"
df_weather = pd.read_sql(query, conn)
conn.close()

# 🔶 전처리
df_weather['일시'] = pd.to_datetime(df_weather['일시'], errors='coerce')
df_weather['연월'] = df_weather['일시'].dt.to_period('M').astype(str)

# 🔶 연월 선택
available_months = sorted(df_weather['연월'].unique(), reverse=True)
selected_month = st.selectbox("📅 기준 월 선택", available_months)

# 🔶 선택 월 필터링
df_selected = df_weather[df_weather['연월'] == selected_month]

# 🔶 적합도 계산 (온도 12~18, 습도 60~85, 일조 180 이상)
df_selected['적합도점수'] = 0
df_selected['적합도점수'] += df_selected['평균기온(°C)'].apply(lambda x: 33 if 12 <= x <= 18 else 0)
df_selected['적합도점수'] += df_selected['평균 상대습도(%)'].apply(lambda x: 33 if 60 <= x <= 85 else 0)
df_selected['일조시간'] = pd.to_numeric(df_selected['일조시간'], errors='coerce')
df_selected['적합도점수'] += df_selected['일조시간'].apply(lambda x: 34 if x >= 180 else 0)

df_selected['적합여부'] = df_selected['적합도점수'].apply(lambda x: '적합' if x >= 66 else '부적합')

# 🔶 지도 생성
m = folium.Map(location=[33.5, 126.5], zoom_start=10)

# 🔶 마커 및 색상 표시
for _, row in df_selected.iterrows():
    region = row['지점명']
    if region in coord_dict:
        lat, lon = coord_dict[region][1], coord_dict[region][0]
        status = row['적합여부']
        color = 'green' if status == '적합' else 'gray'

        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
            color=color,
            fill=True,
            fill_opacity=0.7,
            tooltip=f"{region} ({status})\n기온: {row['평균기온(°C)']}°C\n습도: {row['평균 상대습도(%)']}%\n일조: {row['일조시간']}시간"
        ).add_to(m)

# 🔶 지도 출력
st.subheader(f"🗺️ 감귤 재배 적합도 지도 ({selected_month})")
st_folium(m, width=800, height=600)

# 🔶 요약 표 출력
st.subheader("📊 적합도 세부 데이터")
st.dataframe(df_selected[['지점명', '평균기온(°C)', '평균 상대습도(%)', '일조시간', '적합도점수', '적합여부']])
