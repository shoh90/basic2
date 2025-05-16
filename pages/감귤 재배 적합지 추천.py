import streamlit as st
import pandas as pd
import folium
import sqlite3  # ✅ 반드시 import 필요
from streamlit_folium import st_folium

# ✅ 페이지 설정
st.set_page_config(page_title="감귤 재배 적합지 추천", layout="wide", page_icon="🍊")

st.title("🍊 감귤 재배 적합지 추천")
st.markdown("제주도 주요 지역의 감귤 재배량과 재배 적합도를 지도에서 확인하세요.")

# ✅ 데이터 로딩 함수
@st.cache_data
def load_data():
    # 기상 DB
    df_weather = pd.read_sql("SELECT * FROM asos_weather", sqlite3.connect('data/asos_weather.db'))

    # 감귤 재배량 & 좌표
    df_citrus = pd.read_excel('data/5.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})
    df_coords = pd.read_excel('data/coords.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})
    return df_weather, df_citrus, df_coords

df_weather, df_citrus, df_coords = load_data()

# ✅ 데이터 전처리
df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['월'] = df_weather['일시'].dt.month
df_weather['연도'] = df_weather['일시'].dt.year

prod_cols = ['노지온주(극조생)', '노지온주(조생)', '노지온주(보통)', '하우스감귤(조기출하)',
             '비가림(월동)감귤', '만감류(시설)', '만감류(노지)']
df_citrus['총재배량(톤)'] = df_citrus[prod_cols].sum(axis=1, numeric_only=True)

# ✅ 연도 선택
available_years = sorted(df_citrus['연도'].dropna().unique(), reverse=True)
selected_year = st.selectbox("확인할 연도를 선택하세요", available_years)

# ✅ 데이터 병합
df_weather_agg = df_weather[df_weather['연도'] == selected_year].groupby('지점명').agg({
    '평균기온(°C)': 'mean',
    '평균상대습도(%)': 'mean',
    '월합강수량(00~24h만)(mm)': 'sum',
    '평균풍속(m/s)': 'mean',
    '합계 일조시간(hr)': 'sum'
}).reset_index().rename(columns={'지점명': '읍면동'})

df_coords['읍면동'] = df_coords['읍면동'].str.strip()
df_citrus['읍면동'] = df_citrus['읍면동'].str.strip()

df = df_weather_agg.merge(df_citrus[['읍면동', '총재배량(톤)']], on='읍면동', how='inner')
df = df.merge(df_coords, on='읍면동', how='left')

# ✅ 적합도 기준
df['기온적합'] = df['평균기온(°C)'].apply(lambda x: 1 if 15 <= x <= 25 else 0)
df['습도적합'] = df['평균상대습도(%)'].apply(lambda x: 1 if 60 <= x <= 80 else 0)
df['강수적합'] = df['월합강수량(00~24h만)(mm)'].apply(lambda x: 1 if 30 <= x <= 100 else 0)
df['풍속적합'] = df['평균풍속(m/s)'].apply(lambda x: 1 if x <= 4 else 0)
df['일조적합'] = df['합계 일조시간(hr)'].apply(lambda x: 1 if x >= 150 else 0)

df['적합도점수'] = df[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
df['결과'] = df['적합도점수'].apply(lambda x: '적합' if x == 5 else '부적합')

# ✅ 지도 시각화
st.subheader(f"🌍 {selected_year} 기준 감귤 재배량 및 적합도 지도")

m = folium.Map(location=[33.4, 126.5], zoom_start=10)

for _, row in df.iterrows():
    if pd.notnull(row['위도']) and pd.notnull(row['경도']):
        color = 'green' if row['결과'] == '적합' else 'red'
        folium.CircleMarker(
            location=[row['위도'], row['경도']],
            radius=8,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=f"{row['읍면동']} ({row['결과']})\n재배량: {row['총재배량(톤)']}톤"
        ).add_to(m)

st_folium(m, width=1000, height=600)

# ✅ 적합 지역 요약
st.write("📝 적합 지역 요약")
st.dataframe(df[df['결과'] == '적합'][['읍면동', '총재배량(톤)', '평균기온(°C)', '평균상대습도(%)', '월합강수량(00~24h만)(mm)', '평균풍속(m/s)', '합계 일조시간(hr)']])
