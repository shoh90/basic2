import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="제주 감귤 재배 적합도", layout="wide")

st.title("🍊 제주 감귤 재배 적합도 종합 지도")

# ✅ 월 선택
month = st.selectbox("월을 선택하세요", list(range(1, 13)))

# ✅ 데이터 로딩 (기온, 습도, 강수량 등)
# (여기서는 가상으로 예시 df로 표현)
df_weather = pd.read_csv('data/sample_weather.csv')  # 기온, 습도, 강수량, 바람
df_sun = pd.read_csv('data/sample_sunshine.csv')    # 일조시간
df_pest = pd.read_csv('data/sample_pest.csv')       # 병해충 위험도
df_citrus = pd.read_excel('data/5.xlsx')            # 재배량
df_coords = pd.read_excel('data/coords.xlsx')       # 좌표

# ✅ 적합도 계산 (항목별)
df_weather['기온적합'] = df_weather['평균기온'] .apply(lambda x: 1 if 18 <= x <= 25 else 0)
df_weather['습도적합'] = df_weather['평균습도'] .apply(lambda x: 1 if 60 <= x <= 75 else 0)
df_weather['강수적합'] = df_weather['강수량'] .apply(lambda x: 1 if x <= 50 else 0)
df_weather['바람적합'] = df_weather['풍속'] .apply(lambda x: 1 if x <= 5 else 0)
df_sun['일조적합'] = df_sun['일조시간'].apply(lambda x: 1 if x >= 6 else 0)
df_pest['병해적합'] = df_pest['위험도지수'].apply(lambda x: 1 if x <= 0.5 else 0)

# ✅ 통합 적합도 (읍면동 단위)
df = df_weather.merge(df_sun, on='읍면동').merge(df_pest, on='읍면동').merge(df_citrus, on='읍면동')
df['적합도'] = df[['기온적합', '습도적합', '강수적합', '바람적합', '일조적합', '병해적합']].mean(axis=1)
df['결과'] = df['적합도'].apply(lambda x: "적합" if x >= 0.7 else "부적합")

# ✅ 지도 시각화
m = folium.Map(location=[33.5, 126.5], zoom_start=10)

for idx, row in df.iterrows():
    coord = df_coords[df_coords['행정구역(읍면동)'] == row['읍면동']]
    if not coord.empty:
        lat, lon = coord.iloc[0]['위도'], coord.iloc[0]['경도']
        color = 'green' if row['결과'] == '적합' else 'red'
        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
            color=color,
            fill=True,
            fill_opacity=0.6,
            popup=f"{row['읍면동']}\n재배량: {row['재배량(톤)']}톤\n적합도: {row['적합도']:.2f}",
            tooltip=row['결과']
        ).add_to(m)

st_folium(m, width=1000, height=700)
