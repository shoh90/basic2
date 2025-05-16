import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(page_title="감귤 재배 적합지 추천", layout="wide", page_icon="🍊")

st.title("🍊 감귤 재배 적합지 추천")
st.markdown("제주도 주요 지역의 감귤 재배량과 재배 적합도를 지도에서 확인하세요.")

# ----------------- 데이터 로딩 -----------------
@st.cache_data
def load_data():
    df_weather = pd.read_sql("SELECT * FROM asos_weather", sqlite3.connect('data/asos_weather.db'))
    df_citrus_1 = pd.read_excel('data/5.xlsx', engine='openpyxl')
    df_citrus_2 = pd.read_excel('data/4.xlsx', engine='openpyxl')
    df_coords = pd.read_excel('data/coords.xlsx', engine='openpyxl')
    return df_weather, df_citrus_1, df_citrus_2, df_coords

df_weather, df_citrus_1, df_citrus_2, df_coords = load_data()

# ----------------- 데이터 준비 -----------------
# 좌표 dict
df_coords = df_coords.rename(columns={'행정구역(읍면동)': '읍면동'})
coord_dict = df_coords.set_index("읍면동").T.to_dict()

# 연도 선택 (두 데이터 모두 포함된 범위)
years_1 = df_citrus_1['연도'].dropna().unique()
years_2 = df_citrus_2['연도'].dropna().unique()
available_years = sorted(set(years_1) | set(years_2), reverse=True)

selected_year = st.selectbox("확인할 연도를 선택하세요", available_years)

# ----------------- 지도 생성 -----------------
map_center = [33.5, 126.5]
m = folium.Map(location=map_center, zoom_start=10)

# 첫 번째 데이터 마커
filtered_1 = df_citrus_1[df_citrus_1['연도'] == selected_year]
for _, row in filtered_1.iterrows():
    region = row['읍면동']
    crops = {col: row[col] for col in ['노지온주(극조생)', '노지온주(조생)', '노지온주(보통)',
                                        '하우스감귤(조기출하)', '비가림(월동)감귤',
                                        '만감류(시설)', '만감류(노지)']}
    if region in coord_dict:
        lat, lon = coord_dict[region]['위도'], coord_dict[region]['경도']
        detail = "\n".join([f"{crop}: {amount:,.2f}톤" for crop, amount in crops.items()])
        folium.Marker(
            location=[lat, lon],
            popup=f"{region}\n{detail}",
            tooltip=region,
            icon=folium.Icon(color='blue')
        ).add_to(m)

# 두 번째 데이터 마커
filtered_2 = df_citrus_2[df_citrus_2['연도'] == selected_year]
for _, row in filtered_2.iterrows():
    region = row['행정구역(읍면동)']
    amount = row['재배량(톤)']
    if region in coord_dict:
        lat, lon = coord_dict[region]['위도'], coord_dict[region]['경도']
        folium.Marker(
            location=[lat, lon],
            popup=f"{region}: 감귤 {amount:,}톤",
            tooltip=region,
            icon=folium.Icon(color='green')
        ).add_to(m)

# ----------------- 지도 출력 -----------------
st.subheader(f"🌍 {selected_year} 기준 감귤 재배량 지도")
st_folium(m, width=1000, height=600)
