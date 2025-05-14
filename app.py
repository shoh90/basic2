import streamlit as st
import folium
import pandas as pd
import sqlite3
import json
from streamlit_folium import st_folium

# 🔶 페이지 설정
st.set_page_config(page_title="제주 감귤 재배 적합도", layout="wide")

# 🔶 파일 경로 설정 (data 폴더 기준)
db_path = "data/asos_weather.db"
geojson_path = "data/jeju_geo.json"

# 🔶 GeoJSON 좌표 데이터 로딩
try:
    with open(geojson_path, encoding='utf-8') as f:
        geo_data = json.load(f)
    coord_dict = {f['properties']['name']: f['geometry']['coordinates'] for f in geo_data['features'] if f['properties']['name']}
except FileNotFoundError:
    st.error(f"❌ geojson 파일이 없습니다: {geojson_path}")
    st.stop()

# 🔶 DB 데이터 로딩
try:
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM asos_weather"
    df_weather = pd.read_sql(query, conn)
    conn.close()
except Exception as e:
    st.error(f"❌ DB 파일 오류: {e}")
    st.stop()

# 🔶 컬럼명 확인
st.write("📊 DB 컬럼명 확인:", df_weather.columns.tolist())

# 🔶 전처리: 연월 추가
df_weather['일시'] = pd.to_datetime(df_weather['일시'], errors='coerce')
df_weather['연월'] = df_weather['일시'].dt.to_period('M').astype(str)

# 🔶 연월 선택
available_months = sorted(df_weather['연월'].unique(), reverse=True)
selected_month = st.selectbox("📅 기준 월 선택", available_months)

# 🔶 선택한 월 필터링
df_selected = df_weather[df_weather['연월'] == selected_month]

# 🔶 컬럼명 자동 매칭 (습도, 일조)
humidity_col = next((col for col in df_selected.columns if '습도' in col), None)
sunshine_col = next((col for col in df_selected.columns if '일조' in col), None)

if not humidity_col or not sunshine_col:
    st.error(f"❌ '습도' 또는 '일조' 컬럼이 없습니다. 현재 컬럼명: {df_selected.columns.tolist()}")
    st.stop()

# 🔶 적합도 계산
df_selected['적합도점수'] = 0
df_selected['적합도점수'] += df_selected['평균기온(°C)'].apply(lambda x: 33 if 12 <= x <= 18 else 0)
df_selected['적합도점수'] += df_selected[humidity_col].apply(lambda x: 33 if 60 <= x <= 85 else 0)
df_selected[sunshine_col] = pd.to_numeric(df_selected[sunshine_col], errors='coerce')
df_selected['적합도점수'] += df_selected[sunshine_col].apply(lambda x: 34 if x >= 180 else 0)

df_selected['적합여부'] = df_selected['적합도점수'].apply(lambda x: '적합' if x >= 66 else '부적합')

# 🔶 folium 지도 생성
m = folium.Map(location=[33.5, 126.5], zoom_start=10)

# 🔶 CircleMarker 표시
for _, row in df_selected.iterrows():
    region = row['지점명']
    if region in coord_dict:
        lat, lon = coord_dict[region][1], coord_dict[region][0]
        status = row['적합여부']
        color = 'green' if status == '적합' else 'gray'

        tooltip_text = (
            f"{region} ({status})\n"
            f"기온: {row['평균기온(°C)']}°C\n"
            f"습도: {row[humidity_col]}%\n"
            f"일조: {row[sunshine_col]}시간"
        )

        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
            color=color,
            fill=True,
            fill_opacity=0.7,
            tooltip=tooltip_text
        ).add_to(m)

# 🔶 지도 출력
st.subheader(f"🗺️ 감귤 재배 적합도 지도 ({selected_month})")
st_folium(m, width=800, height=600)

# 🔶 적합도 세부 데이터 출력
st.subheader("📊 적합도 세부 데이터")
st.dataframe(df_selected[['지점명', '평균기온(°C)', humidity_col, sunshine_col, '적합도점수', '적합여부']])
