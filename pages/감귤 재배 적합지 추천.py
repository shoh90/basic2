import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

# --- 페이지 설정 ---
st.set_page_config(page_title="감귤 재배 적합지 추천", layout="wide", page_icon="🍊")

st.title("🍊 감귤 재배 적합지 추천")
st.markdown("제주도 주요 지역의 감귤 재배량과 재배 적합도를 지도를 통해 확인하세요.")

# --- 데이터 로딩 ---
@st.cache_data
def load_data():
    df_weather = pd.read_sql("SELECT * FROM asos_weather", sqlite3.connect('data/asos_weather.db'))
    df_citrus = pd.read_excel('data/5.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})
    df_coords = pd.read_excel('data/coords.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})
    return df_weather, df_citrus, df_coords

df_weather, df_citrus, df_coords = load_data()

# --- 전처리 ---
df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['월'] = df_weather['일시'].dt.month
df_weather['연도'] = df_weather['일시'].dt.year

# 감귤 총재배량
prod_cols = ['노지온주(극조생)', '노지온주(조생)', '노지온주(보통)', '하우스감귤(조기출하)',
             '비가림(월동)감귤', '만감류(시설)', '만감류(노지)']
df_citrus['총재배량(톤)'] = df_citrus[prod_cols].sum(axis=1, numeric_only=True)

# --- 관측소 좌표 (예시 좌표 사용, 실제 더 정확한 좌표 필요) ---
observatory_locations = {
    '제주시': (33.51411, 126.52919),
    '고산': (33.29382, 126.16283),
    '성산': (33.46483, 126.91336),
    '서귀포시': (33.24616, 126.56530)
}
df_observatory_coords = pd.DataFrame.from_dict(observatory_locations, orient='index', columns=['관측소_위도', '관측소_경도']).reset_index().rename(columns={'index': '지점명'})

# --- 읍면동 → 최근접 관측소 동적 매핑 ---
def find_nearest_observatory(lat, lon, observatories_df):
    if pd.isna(lat) or pd.isna(lon):
        return '제주시'
    distances = observatories_df.apply(
        lambda row: geodesic((lat, lon), (row['관측소_위도'], row['관측소_경도'])).km,
        axis=1
    )
    nearest_idx = distances.idxmin()
    return observatories_df.loc[nearest_idx, '지점명']

df_coords['지점명'] = df_coords.apply(lambda row: find_nearest_observatory(row['위도'], row['경도'], df_observatory_coords), axis=1)

# --- 연도 선택 ---
available_years = sorted(df_citrus['연도'].dropna().unique(), reverse=True)
selected_year = st.selectbox("확인할 연도를 선택하세요", available_years, index=0)

# --- 기상 데이터 집계 ---
df_weather_year = df_weather[df_weather['연도'] == selected_year]
df_weather_agg = df_weather_year.groupby('지점명').agg({
    '평균기온(°C)': 'mean',
    '평균상대습도(%)': 'mean',
    '월합강수량(00~24h만)(mm)': 'sum',
    '평균풍속(m/s)': 'mean',
    '합계 일조시간(hr)': 'sum'
}).reset_index()

# --- 병합 ---
df_base = df_coords.merge(df_citrus[df_citrus['연도'] == selected_year], on='읍면동', how='left')
df_base = df_base.merge(df_weather_agg, on='지점명', how='left')

# --- 적합도 계산 ---
df_base['기온적합'] = df_base['평균기온(°C)'].apply(lambda x: 1 if 15 <= x <= 25 else 0)
df_base['습도적합'] = df_base['평균상대습도(%)'].apply(lambda x: 1 if 60 <= x <= 80 else 0)
df_base['강수적합'] = df_base['월합강수량(00~24h만)(mm)'].apply(lambda x: 1 if 50 <= x <= 200 else 0)
df_base['풍속적합'] = df_base['평균풍속(m/s)'].apply(lambda x: 1 if x <= 3.4 else 0)
df_base['일조적합'] = df_base['합계 일조시간(hr)'].apply(lambda x: 1 if x >= 150 else 0)

df_base['적합도점수'] = df_base[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
df_base['결과'] = df_base['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('보통' if x >= 3 else '부적합'))

# --- 지도 시각화 ---
st.subheader(f"🗺️ {selected_year} 기준 감귤 재배량 및 적합도 지도")
m = folium.Map(location=[33.4, 126.5], zoom_start=10)
for _, row in df_base.iterrows():
    if pd.notnull(row['위도']) and pd.notnull(row['경도']):
        color = 'green' if row['결과'] == '적합' else ('orange' if row['결과'] == '보통' else 'red')
        folium.CircleMarker(
            location=[row['위도'], row['경도']],
            radius=8,
            color=color,
            fill=True,
            fill_opacity=0.7,
            tooltip=f"{row['읍면동']} - {row['결과']}"
        ).add_to(m)

st_folium(m, width=1000, height=600)

# --- 적합 지역 요약 ---
st.subheader("📋 적합 지역 요약")
df_summary = df_base[df_base['결과'] == '적합'][['읍면동', '총재배량(톤)', '평균기온(°C)', '평균상대습도(%)', '월합강수량(00~24h만)(mm)', '평균풍속(m/s)', '합계 일조시간(hr)']]
st.dataframe(df_summary if not df_summary.empty else pd.DataFrame(columns=['읍면동', '총재배량(톤)', '평균기온(°C)', '평균상대습도(%)', '월합강수량(00~24h만)(mm)', '평균풍속(m/s)', '합계 일조시간(hr)']))
