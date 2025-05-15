import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(page_title="제주 농부 스마트 대시보드", layout="wide", page_icon="🍊")

st.title("🍊 제주 농부 스마트 대시보드")
st.markdown("제주도 농사에 필요한 모든 정보를 한 곳에서 확인하세요.")

# 데이터 로딩
@st.cache_data
def load_data():
    df_weather = pd.read_sql("SELECT * FROM asos_weather", sqlite3.connect('data/asos_weather.db'))
    df_citrus = pd.read_excel('data/5.xlsx')
    df_coords = pd.read_excel('data/coords.xlsx')
    df_pest = pd.concat([pd.read_csv(f'data/pest_disease_info_{i}.csv') for i in range(1, 4)], ignore_index=True)
    return df_weather, df_citrus, df_coords, df_pest

df_weather, df_citrus, df_coords, df_pest = load_data()

# 데이터 전처리
df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['월'] = df_weather['일시'].dt.month
df_weather = df_weather.rename(columns={'지점명': '읍면동'})
df_coords = df_coords.rename(columns={'행정구역(읍면동)': '읍면동'})
df_citrus = df_citrus.rename(columns={'행정구역(읍면동)': '읍면동'})

# 읍면동 공백제거
for df in [df_weather, df_coords, df_citrus]:
    df['읍면동'] = df['읍면동'].str.strip().str.replace(' ', '')

# 총재배량 계산
prod_cols = ['노지온주(극조생)', '노지온주(조생)', '노지온주(보통)', '하우스감귤(조기출하)', '비가림(월동)감귤', '만감류(시설)', '만감류(노지)']
df_citrus['총재배량(톤)'] = df_citrus[prod_cols].sum(axis=1)

# 사용자 선택
years = sorted(df_citrus['연도'].unique(), reverse=True)
selected_year = st.selectbox("기준 연도", years)
selected_month = st.selectbox("기준 월", list(range(1, 13)))

# 필터 버튼 추가 (적합도 결과 필터링)
filter_options = st.multiselect("적합도 결과 필터", ['적합', '보통', '부적합'], default=['적합', '보통', '부적합'])

# 데이터 필터링
df_weather_sel = df_weather[df_weather['월'] == selected_month]
df_citrus_sel = df_citrus[df_citrus['연도'] == selected_year]

# 월별 기상 데이터 집계
df_weather_agg = df_weather_sel.groupby('읍면동').agg({
    '평균기온(°C)': 'mean',
    '평균상대습도(%)': 'mean',
    '월합강수량(00~24h만)(mm)': 'sum',
    '평균풍속(m/s)': 'mean',
    '합계 일조시간(hr)': 'sum'
}).reset_index()

# 병합
df_merge = df_coords.merge(df_weather_agg, on='읍면동', how='left')
df_merge = df_merge.merge(df_citrus_sel[['읍면동', '총재배량(톤)']], on='읍면동', how='left')

# 적합도 계산
df_merge['기온적합'] = df_merge['평균기온(°C)'].apply(lambda x: 1 if 18 <= x <= 25 else 0)
df_merge['습도적합'] = df_merge['평균상대습도(%)'].apply(lambda x: 1 if 60 <= x <= 75 else 0)
df_merge['강수적합'] = df_merge['월합강수량(00~24h만)(mm)'].apply(lambda x: 1 if x <= 50 else 0)
df_merge['풍속적합'] = df_merge['평균풍속(m/s)'].apply(lambda x: 1 if x <= 5 else 0)
df_merge['일조적합'] = df_merge['합계 일조시간(hr)'].apply(lambda x: 1 if x >= 6 else 0)

df_merge['적합도점수'] = df_merge[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
df_merge['결과'] = df_merge['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('보통' if x >= 2 else '부적합'))

# 필터링 반영
df_merge = df_merge[df_merge['결과'].isin(filter_options)]

# 지도 시각화
m = folium.Map(location=[33.4, 126.5], zoom_start=10)
for _, row in df_merge.iterrows():
    if pd.notnull(row['위도']) and pd.notnull(row['경도']):
        color = 'green' if row['결과'] == '적합' else ('orange' if row['결과'] == '보통' else 'red')
        folium.CircleMarker(
            location=[row['위도'], row['경도']],
            radius=8,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=f"{row['읍면동']} ({row['결과']})\n재배량: {row['총재배량(톤)']:.1f}톤"
        ).add_to(m)

st.subheader(f"{selected_year}년 {selected_month}월 재배 적합도")
st_folium(m, width=1000, height=600)

# 병해충 방제약 정보
st.subheader("🐛 병해충 방제약 정보")
if not df_pest.empty:
    st.dataframe(df_pest[['중점방제대상', '병해충', '방제약', '데이터기준일자']])
else:
    st.warning("병해충 데이터를 불러오지 못했습니다.")
