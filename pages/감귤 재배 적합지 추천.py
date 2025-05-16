import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(page_title="감귤 재배 적합지 추천", layout="wide", page_icon="🍊")

st.title("🍊 감귤 재배 적합지 추천")
st.markdown("제주도 주요 지역의 감귤 재배량과 재배 적합도를 지도에서 확인하세요.")

# ----------------- 데이터 로딩 -----------------
@st.cache_data
def load_data():
    conn = sqlite3.connect('data/asos_weather.db')
    df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
    conn.close()
    df_citrus_1 = pd.read_excel('data/5.xlsx', engine='openpyxl')
    df_citrus_2 = pd.read_excel('data/4.xlsx', engine='openpyxl')
    df_coords = pd.read_excel('data/coords.xlsx', engine='openpyxl')
    return df_weather, df_citrus_1, df_citrus_2, df_coords

df_weather, df_citrus_1, df_citrus_2, df_coords = load_data()

df_coords = df_coords.rename(columns={'행정구역(읍면동)': '읍면동'})
coord_dict = df_coords.set_index("읍면동").T.to_dict()

# 연도 선택
years_1 = df_citrus_1['연도'].dropna().unique()
years_2 = df_citrus_2['연도'].dropna().unique()
available_years = sorted(set(years_1) | set(years_2), reverse=True)

selected_year = st.selectbox("확인할 연도를 선택하세요", available_years)

# ----------------- 지도 생성 -----------------
map_center = [33.5, 126.5]
m = folium.Map(location=map_center, zoom_start=10)

# ----------------- 병합된 데이터 기반 적합도 계산 -----------------
df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['월'] = df_weather['일시'].dt.month
df_weather['연도'] = df_weather['일시'].dt.year

# 월별 요약 (전체 평균)
weather_month = df_weather[df_weather['연도'] == selected_year].groupby('지점명').agg({
    '평균기온(°C)': 'mean',
    '평균상대습도(%)': 'mean',
    '월합강수량(00~24h만)(mm)': 'mean',
    '평균풍속(m/s)': 'mean',
    '합계 일조시간(hr)': 'mean'
}).reset_index().rename(columns={'지점명': '읍면동'})

# 적합도 계산
weather_month['기온적합'] = weather_month['평균기온(°C)'].apply(lambda x: 1 if 18 <= x <= 25 else 0)
weather_month['습도적합'] = weather_month['평균상대습도(%)'].apply(lambda x: 1 if 60 <= x <= 75 else 0)
weather_month['강수적합'] = weather_month['월합강수량(00~24h만)(mm)'].apply(lambda x: 1 if x <= 50 else 0)
weather_month['풍속적합'] = weather_month['평균풍속(m/s)'].apply(lambda x: 1 if x <= 5 else 0)
weather_month['일조적합'] = weather_month['합계 일조시간(hr)'].apply(lambda x: 1 if x >= 150 else 0)

weather_month['적합도점수'] = weather_month[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
weather_month['결과'] = weather_month['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('보통' if x >= 2 else '부적합'))

# ----------------- 첫 번째 데이터 마커 -----------------
filtered_1 = df_citrus_1[df_citrus_1['연도'] == selected_year]
for _, row in filtered_1.iterrows():
    region = row['읍면동']
    crops = {col: row[col] for col in ['노지온주(극조생)', '노지온주(조생)', '노지온주(보통)',
                                        '하우스감귤(조기출하)', '비가림(월동)감귤',
                                        '만감류(시설)', '만감류(노지)'] if col in row}
    if region in coord_dict:
        lat, lon = coord_dict[region]['위도'], coord_dict[region]['경도']
        # 적합도 점수 가져오기
        result = weather_month[weather_month['읍면동'] == region]['결과'].values[0] if region in weather_month['읍면동'].values else '정보없음'
        color = 'green' if result == '적합' else ('orange' if result == '보통' else 'red')
        detail = "\n".join([f"{crop}: {amount:,.2f}톤" for crop, amount in crops.items()])
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=color,
            fill=True,
            fill_opacity=0.7,
            tooltip=f"{region} - {result}\n{detail}"
        ).add_to(m)

# ----------------- 두 번째 데이터 마커 -----------------
filtered_2 = df_citrus_2[df_citrus_2['연도'] == selected_year]
for _, row in filtered_2.iterrows():
    region = row['행정구역(읍면동)']
    amount = row['재배량(톤)']
    if region in coord_dict:
        lat, lon = coord_dict[region]['위도'], coord_dict[region]['경도']
        result = weather_month[weather_month['읍면동'] == region]['결과'].values[0] if region in weather_month['읍면동'].values else '정보없음'
        color = 'green' if result == '적합' else ('orange' if result == '보통' else 'red')
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=color,
            fill=True,
            fill_opacity=0.7,
            tooltip=f"{region} - {result}\n재배량: {amount:,.2f}톤"
        ).add_to(m)

# ----------------- 지도 출력 -----------------
st.subheader(f"🌍 {selected_year} 기준 감귤 재배량 및 적합도 지도")
st_folium(m, width=1000, height=600)
