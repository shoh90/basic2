import streamlit as st
import folium
import pandas as pd
import geopandas as gpd
from streamlit_folium import st_folium

# 1. 행정구역 GeoJSON 파일 불러오기
geojson_path = "jeju_eupmyeondong.geojson"  # 🟡 GeoJSON 파일 경로
gdf = gpd.read_file(geojson_path)

# 2. 기존 데이터 불러오기 (df_merge 예시)
# df_merge = 기존 적합성 데이터프레임 (지점명, 적합여부 포함)

# 3. GeoDataFrame에 '적합여부' 병합
gdf = gdf.merge(df_merge[['지점명', '적합여부']], left_on='읍면동명', right_on='지점명', how='left')

# 4. 색상 매핑 함수
def get_color(grade):
    if pd.isna(grade):
        return 'lightgray'  # 데이터 없음
    elif grade == '적합':
        return 'green'
    else:
        return 'gray'

# 5. 지도 생성
m = folium.Map(location=[33.5, 126.5], zoom_start=10)

# 6. 행정구역 폴리곤 시각화
for _, row in gdf.iterrows():
    folium.GeoJson(
        row['geometry'],
        style_function=lambda feature, color=get_color(row['적합여부']): {
            'fillColor': color,
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.5,
        },
        tooltip=row['읍면동명']
    ).add_to(m)

# 7. 기존 마커도 함께 추가
# (위에서 쓰던 successful_locations_1, 2 반복문 그대로 쓰면 됩니다.)

# 8. Streamlit 지도 출력
st.subheader("🗺️ 감귤 적합도 지도 (행정구역 경계 포함)")
st_folium(m, width=700, height=500)
