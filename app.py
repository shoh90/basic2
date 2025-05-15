import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium

# ✅ 페이지 설정
st.set_page_config(page_title="제주 농부 스마트 대시보드", layout="wide", page_icon="🍊")

# ✅ 대시보드 소개
st.title("🍊 제주 농부 스마트 대시보드")
st.markdown("""
제주도 농사에 필요한 모든 정보를 한 곳에서 확인하세요.  
왼쪽 메뉴에서 원하는 항목을 선택하세요.
""")

# ✅ 카드형 메뉴
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("🏠 전체 요약")
with col2:
    st.subheader("📊 기후 분석")
with col3:
    st.subheader("🥕 작물 맞춤 조언")

st.divider()

# ✅ 월 선택
month = st.selectbox("확인할 월을 선택하세요", list(range(1, 13)))

# ✅ 데이터 로딩
conn = sqlite3.connect('data/asos_weather.db')
df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
conn.close()

df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['월'] = df_weather['일시'].dt.month

df_citrus = pd.read_excel('data/5.xlsx')
df_coords = pd.read_excel('data/coords.xlsx')

# ✅ 좌표 Key 안전판
st.write("🗺️ df_coords 컬럼명:", df_coords.columns.tolist())
coord_key_col = next((col for col in ['읍면동', '행정구역(읍면동)', '지점명'] if col in df_coords.columns), None)
if not coord_key_col:
    st.error("❗ df_coords에서 사용할 수 있는 읍면동 Key 컬럼이 없습니다.")
    st.stop()
df_coords = df_coords.rename(columns={coord_key_col: '읍면동'})

# ✅ df_weather Key 안전판
st.write("📊 df_weather 컬럼명:", df_weather.columns.tolist())
weather_key_col = next((col for col in ['읍면동', '행정구역(읍면동)', '지점명'] if col in df_weather.columns), None)
if not weather_key_col:
    st.error("❗ df_weather에서 사용할 수 있는 읍면동 Key 컬럼이 없습니다.")
    st.stop()

# ✅ 재배량 합계
df_citrus = df_citrus.rename(columns={'행정구역(읍면동)': '읍면동'})
df_citrus['총재배량(톤)'] = df_citrus[[
    '노지온주(극조생)', '노지온주(조생)', '노지온주(보통)',
    '하우스감귤(조기출하)', '비가림(월동)감귤',
    '만감류(시설)', '만감류(노지)'
]].sum(axis=1)

# ✅ 월별 기상 데이터 집계 (Key 안전판 적용)
df_weather_month = df_weather[df_weather['월'] == month].groupby(weather_key_col).agg({
    '평균기온(°C)': 'mean',
    '평균상대습도(%)': 'mean',
    '월합강수량(00~24h만)(mm)': 'sum',
    '평균풍속(m/s)': 'mean',
    '합계 일조시간(hr)': 'sum'
}).reset_index().rename(columns={weather_key_col: '읍면동'})

# ✅ 데이터 병합
df = df_weather_month.merge(df_citrus[['읍면동', '총재배량(톤)']], on='읍면동', how='left')
df = df.merge(df_coords, on='읍면동', how='left')

# ✅ 적합도 계산
df['기온적합'] = df['평균기온(°C)'].apply(lambda x: 1 if 18 <= x <= 25 else 0)
df['습도적합'] = df['평균상대습도(%)'].apply(lambda x: 1 if 60 <= x <= 75 else 0)
df['강수적합'] = df['월합강수량(00~24h만)(mm)'].apply(lambda x: 1 if x <= 50 else 0)
df['풍속적합'] = df['평균풍속(m/s)'].apply(lambda x: 1 if x <= 5 else 0)
df['일조적합'] = df['합계 일조시간(hr)'].apply(lambda x: 1 if x >= 6 else 0)

df['적합도'] = df[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].mean(axis=1)
df['결과'] = df['적합도'].apply(lambda x: '적합' if x >= 0.7 else '부적합')

# ✅ 지도 시각화
m = folium.Map(location=[33.4, 126.5], zoom_start=10)

for idx, row in df.iterrows():
    if pd.notnull(row['위도']) and pd.notnull(row['경도']):
        color = 'green' if row['결과'] == '적합' else 'red'
        folium.CircleMarker(
            location=[row['위도'], row['경도']],
            radius=10,
            color=color,
            fill=True,
            fill_opacity=0.6,
            popup=f"{row['읍면동']}\n재배량: {row['총재배량(톤)']}톤\n적합도: {row['적합도']:.2f}",
            tooltip=row['결과']
        ).add_to(m)

st_folium(m, width=1000, height=600)

# ✅ 병해충 방제약 정보 표시
st.subheader("🐛 주요 병해충 방제약 정보")
df_pest = pd.read_csv('data/pest_disease_4.csv')
st.dataframe(df_pest[['중점방제대상', '병해충', '방제약', '데이터기준일자']])
