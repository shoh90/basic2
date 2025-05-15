import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="제주 감귤 재배 적합도", layout="wide")

st.set_page_config(
    page_title="제주 농부 스마트 대시보드",
    layout="wide",
    page_icon="🍊"
)

# ----------------- 상단 대시보드 소개 -----------------
st.title("🍊 제주 농부 스마트 대시보드")

st.markdown("""
제주도 농사에 필요한 모든 정보를 한 곳에서 확인하세요.  
왼쪽 메뉴에서 원하는 항목을 선택하세요.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🏠 전체 요약")
    st.markdown("오늘 날씨 / 주간 예보 / 감귤 재배량 지도")

with col2:
    st.subheader("📊 기후 & 병해충 분석")
    st.markdown("기온 / 강수량 / 풍속 / 습도 / 일조량 / 병해충 분석")

with col3:
    st.subheader("🥕 작물 맞춤 조언")
    st.markdown("감귤, 배추 등 월별 맞춤형 농업 조언 제공")

st.divider()
st.caption("© 2024 제주 스마트팜 농가 대시보드 | Data: KMA, 제주특별자치도")

# ----------------- 아래 감귤 재배 적합도 지도 -----------------


st.title("🍊 제주 감귤 재배 적합도 종합 지도")

# ✅ 월 선택
month = st.selectbox("확인할 월을 선택하세요", list(range(1, 13)))

# ✅ 데이터 로딩 (예시: 경로 수정)
db_path = 'data/asos_weather.db'
conn = sqlite3.connect(db_path)
df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
conn.close()

df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['월'] = df_weather['일시'].dt.month

df_sun = pd.read_csv('data/sunshine_data.csv')
df_pest = pd.concat([
    pd.read_csv('data/pest_disease_info_1.csv'),
    pd.read_csv('data/pest_disease_info_2.csv'),
    pd.read_csv('data/pest_disease_info_3.csv')
])

df_citrus = pd.read_excel('data/5.xlsx')
df_coords = pd.read_excel('data/coords.xlsx')

# ✅ 월별 평균값 추출 (기온, 습도, 강수량, 풍속)
weather_monthly = df_weather[df_weather['월'] == month].groupby('지점명').agg({
    '평균기온(°C)': 'mean',
    '평균 상대습도(%)': 'mean',
    '일강수량(mm)': 'sum',
    '평균 풍속(m/s)': 'mean'
}).reset_index()

# ✅ 일조량 데이터 병합
sun_monthly = df_sun[df_sun['월'] == month][['읍면동', '일조시간(hr)']]

# ✅ 병해충 위험도 평균
df_pest['데이터기준일자'] = pd.to_datetime(df_pest['데이터기준일자'])
df_pest['월'] = df_pest['데이터기준일자'].dt.month
pest_monthly = df_pest[df_pest['월'] == month].groupby('중점방제대상').agg({
    '위험도지수': 'mean'
}).reset_index()

# ✅ 병합 (읍면동 기준)
df = weather_monthly.rename(columns={'지점명': '읍면동'}).merge(sun_monthly, on='읍면동', how='left')
df = df.merge(df_citrus[['읍면동', '재배량(톤)']], on='읍면동', how='left')
df = df.merge(df_coords, on='읍면동', how='left')
df = df.merge(pest_monthly.rename(columns={'중점방제대상': '읍면동'}), on='읍면동', how='left')

# ✅ 적합도 계산
df['기온적합'] = df['평균기온(°C)'].apply(lambda x: 1 if 18 <= x <= 25 else 0)
df['습도적합'] = df['평균 상대습도(%)'].apply(lambda x: 1 if 60 <= x <= 75 else 0)
df['강수적합'] = df['일강수량(mm)'].apply(lambda x: 1 if x <= 50 else 0)
df['풍속적합'] = df['평균 풍속(m/s)'].apply(lambda x: 1 if x <= 5 else 0)
df['일조적합'] = df['일조시간(hr)'].apply(lambda x: 1 if x >= 6 else 0)
df['병해적합'] = df['위험도지수'].apply(lambda x: 1 if pd.notnull(x) and x <= 0.5 else 0)

df['적합도'] = df[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합', '병해적합']].mean(axis=1)
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
            popup=f"{row['읍면동']}\n재배량: {row['재배량(톤)']}톤\n적합도: {row['적합도']:.2f}",
            tooltip=row['결과']
        ).add_to(m)

st_folium(m, width=1000, height=600)

# ✅ 지도 표시
st_folium(m, width=1000, height=600)
