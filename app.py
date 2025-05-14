import streamlit as st
import folium
import pandas as pd
import json
from streamlit_folium import st_folium

# 🔶 Streamlit 페이지 설정
st.set_page_config(page_title="제주 감귤 재배량 시각화", layout="wide")

# 🔶 파일 경로 설정
file_path_1 = "5.xlsx"
file_path_2 = "4.xlsx"
geojson_path = "jeju_geo.json"

# 🔶 데이터 로딩 (5.xlsx)
try:
    data_1 = pd.read_excel(file_path_1, engine='openpyxl')
    if "연도" not in data_1.columns:
        st.error(f"{file_path_1}에 '연도' 컬럼이 없습니다.")
        st.stop()
    data_1_filtered = data_1[data_1["연도"].isin(range(2018, 2023))]
except FileNotFoundError:
    st.error(f"파일을 찾을 수 없습니다: {file_path_1}")
    st.stop()

# 🔶 데이터 로딩 (4.xlsx)
try:
    data_2 = pd.read_excel(file_path_2, engine='openpyxl')
    if "연도" not in data_2.columns:
        st.error(f"{file_path_2}에 '연도' 컬럼이 없습니다.")
        st.stop()
    data_2_filtered = data_2[data_2["연도"].isin(range(2021, 2024))]
except FileNotFoundError:
    st.error(f"파일을 찾을 수 없습니다: {file_path_2}")
    st.stop()

# 🔶 좌표 데이터 (행정구역 포인트 GeoJSON)
try:
    with open(geojson_path, encoding='utf-8') as f:
        geo_data = json.load(f)
    coord_dict = {f['properties']['name']: f['geometry']['coordinates'] for f in geo_data['features'] if f['properties']['name']}
except FileNotFoundError:
    st.error(f"{geojson_path} 파일을 찾을 수 없습니다.")
    st.stop()

# 🔶 연도 선택 (데이터 1, 2 통합)
available_years = sorted(set(data_1_filtered['연도']).union(data_2_filtered['연도']), reverse=True)
selected_year = st.selectbox("📅 연도를 선택하세요:", available_years)

# 🔶 지도 생성
map_center = [33.5, 126.5]
m = folium.Map(location=map_center, zoom_start=10)

# 🔶 데이터1 마커 표시
for _, row in data_1_filtered[data_1_filtered['연도'] == selected_year].iterrows():
    region = row['읍면동']
    if region in coord_dict:
        lat, lon = coord_dict[region][1], coord_dict[region][0]
        crops = {
            '노지온주(극조생)': row['노지온주(극조생)'],
            '노지온주(조생)': row['노지온주(조생)'],
            '노지온주(보통)': row['노지온주(보통)'],
            '하우스감귤(조기출하)': row['하우스감귤(조기출하)'],
            '비가림(월동)감귤': row['비가림(월동)감귤'],
            '만감류(시설)': row['만감류(시설)'],
            '만감류(노지)': row['만감류(노지)']
        }
        crop_details = "\n".join([f"{crop}: {amount:,.2f} 톤" for crop, amount in crops.items()])
        folium.Marker(
            location=[lat, lon],
            popup=f"{region} 재배량\n{crop_details}",
            tooltip=region,
            icon=folium.Icon(color='blue')
        ).add_to(m)

# 🔶 데이터2 마커 표시
for _, row in data_2_filtered[data_2_filtered['연도'] == selected_year].iterrows():
    region = row['행정구역(읍면동)']
    if region in coord_dict:
        lat, lon = coord_dict[region][1], coord_dict[region][0]
        crop_amount = row['재배량(톤)']
        folium.Marker(
            location=[lat, lon],
            popup=f"{region}: 감귤 {crop_amount:,}톤",
            tooltip=region,
            icon=folium.Icon(color='green')
        ).add_to(m)

# 🔶 GeoJSON 포인트 레이어 추가 (행정구역 포인트)
folium.GeoJson(
    geo_data,
    name="행정구역 포인트",
    tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['행정구역명']),
    marker=folium.CircleMarker(radius=6, color='red', fill=True, fill_opacity=0.7)
).add_to(m)

# 🔶 지도 출력
st.title(f"📍 {selected_year} 제주 감귤 재배량 및 행정구역 포인트")
st_folium(m, width=800, height=600)
