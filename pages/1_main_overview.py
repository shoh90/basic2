import streamlit as st
import pandas as pd
import plotly.express as px
import folium
import os
from streamlit_folium import st_folium

from modules.db_loader import load_db_table
from modules.preprocess import preprocess_weather
from modules.unified_utils import get_column

st.set_page_config(layout="wide", page_title="제주 농부 대시보드", page_icon="🍊")

st.title("🏠 제주 농부 대시보드 - 전체 요약")

# ✅ 1. 오늘 날씨 요약
df_weather = load_db_table('asos_weather')
df_weather = preprocess_weather(df_weather)

today = df_weather['일시'].max()
today_data = df_weather[df_weather['일시'] == today]

temp_col = get_column(df_weather, ['기온'])
rain_col = get_column(df_weather, ['강수량'])
wind_col = get_column(df_weather, ['풍속'])

col1, col2, col3 = st.columns(3)
if not today_data.empty:
    col1.metric("🌡 평균기온(°C)", f"{today_data[temp_col].values[0]:.1f}")
    col2.metric("🌧 일강수량(mm)", f"{today_data[rain_col].values[0]:.1f}")
    col3.metric("💨 평균풍속(m/s)", f"{today_data[wind_col].values[0]:.1f}")
else:
    st.warning("❗ 오늘 날짜 데이터가 없습니다.")

# ✅ 2. 주간 강수량 예보 (가상 데이터 함수화)
def get_dummy_forecast(start_date):
    dummy = pd.DataFrame({
        '날짜': pd.date_range(start=start_date, periods=7),
        '예상강수량(mm)': [0, 5, 8, 2, 10, 3, 0]
    })
    return dummy

st.subheader("📅 주간 강수량 예보 (예시)")
dummy_df = get_dummy_forecast(today)
fig = px.bar(dummy_df, x='날짜', y='예상강수량(mm)', title="주간 강수량 예보")
st.plotly_chart(fig)

# ✅ 3. 감귤 재배량 지도 (데이터 로딩 안전성 보강)
st.subheader("📍 제주도 귤 재배량 지도")

data_dir = "data"
try:
    data_1 = pd.read_excel(os.path.join(data_dir, '5.xlsx'), engine='openpyxl')
    data_2 = pd.read_excel(os.path.join(data_dir, '4.xlsx'), engine='openpyxl')
    coords = pd.read_excel(os.path.join(data_dir, 'coords.xlsx'), engine='openpyxl')
except FileNotFoundError as e:
    st.error(f"❗ 데이터 파일을 찾을 수 없습니다: {e}")
    st.stop()

coords_dict = coords.set_index("행정구역(읍면동)")[['위도', '경도']].to_dict(orient='index')

years = sorted(set(data_1['연도'].dropna().unique()) | set(data_2['연도'].dropna().unique()), reverse=True)
selected_year = st.selectbox("연도 선택", years)

m = folium.Map(location=[33.5, 126.5], zoom_start=10)

# ✅ 데이터1 마커
filtered_data_1 = data_1[data_1['연도'] == selected_year]
for _, row in filtered_data_1.iterrows():
    region = row.get('읍면동')
    if not region or region not in coords_dict:
        continue
    lat, lon = coords_dict[region]['위도'], coords_dict[region]['경도']
    crops = {k: row[k] for k in row.keys() if '감귤' in k or '만감류' in k}
    detail_text = "\n".join([f"{k}: {v:,.2f}톤" for k, v in crops.items()])
    folium.Marker(
        location=[lat, lon],
        popup=f"{region}\n{detail_text}",
        tooltip=region,
        icon=folium.Icon(color='blue', icon='leaf', prefix='fa')
    ).add_to(m)

# ✅ 데이터2 마커
filtered_data_2 = data_2[data_2['연도'] == selected_year]
for _, row in filtered_data_2.iterrows():
    region = row.get('행정구역(읍면동)')
    if not region or region not in coords_dict:
        continue
    lat, lon = coords_dict[region]['위도'], coords_dict[region]['경도']
    amount = row.get('재배량(톤)', 0)
    folium.Marker(
        location=[lat, lon],
        popup=f"{region}: 감귤 {amount:,}톤",
        tooltip=region,
        icon=folium.Icon(color='green', icon='map-marker', prefix='fa')
    ).add_to(m)

# ✅ 지도 출력
st_folium(m, width=1000, height=600)
