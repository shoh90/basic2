import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import folium
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(page_title="제주 농부 스마트 대시보드", layout="wide", page_icon="🍊")

st.title("🍊 제주 농부 스마트 대시보드")
st.markdown("제주 농사에 필요한 모든 기능을 **종합적으로 한 페이지에서 확인**하세요.")

# 데이터 로딩
@st.cache_data
def load_data():
    conn = sqlite3.connect('data/asos_weather.db')
    df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
    conn.close()

    df_weather['일시'] = pd.to_datetime(df_weather['일시'])
    df_weather['연도'] = df_weather['일시'].dt.year
    df_weather['월'] = df_weather['일시'].dt.month
    df_weather_recent = df_weather[df_weather['연도'].between(2020, 2024)]
    return df_weather_recent

df_weather_recent = load_data()

# 📊 1. 실시간 기후 모니터링 (예시: 가장 최근 날짜 데이터)
latest_date = df_weather_recent['일시'].max()
df_today = df_weather_recent[df_weather_recent['일시'] == latest_date]

col1, col2 = st.columns(2)
with col1:
    st.subheader(f"🌡 일기온 (최근: {latest_date.date()})")
    fig_temp = px.bar(df_today, x='지점명', y='평균기온(°C)', color='지점명', title='일기온')
    st.plotly_chart(fig_temp, use_container_width=True)

with col2:
    st.subheader(f"🌧 일강수량 (최근: {latest_date.date()})")
    fig_rain = px.bar(df_today, x='지점명', y='일강수량(mm)', color='지점명', title='일강수량')
    st.plotly_chart(fig_rain, use_container_width=True)

# ⚠ 이상기후 경고 (간단 룰 기반)
st.subheader("⚠ 이상기후 경고 (자동 분석)")
if df_today['평균기온(°C)'].mean() > 28:
    st.error("🔥 폭염 경고: 평균기온이 28°C 초과")
if df_today['일강수량(mm)'].mean() < 1:
    st.warning("🌵 가뭄 주의보: 일강수량이 매우 적음")
else:
    st.success("✅ 현재 기후는 안정적입니다.")

# 🗺️ 2. 제주도 종합 감귤 재배 적합도 지도 (최근 연도 11월 기준)
st.subheader("🗺️ 감귤 재배 적합도 지도 (2024년 11월 예시)")

# 연도 월 필터
df_map = df_weather_recent[(df_weather_recent['연도'] == 2024) & (df_weather_recent['월'] == 11)]

# 적합도 계산 (간략화 예시)
df_map['기온적합'] = df_map['평균기온(°C)'].apply(lambda x: 1 if 10 <= x <= 18 else 0)
df_map['적합도'] = df_map['기온적합']
df_map['결과'] = df_map['적합도'].apply(lambda x: '적합' if x == 1 else '부적합')

# 지도 표시
m = folium.Map(location=[33.4, 126.5], zoom_start=9)
for _, row in df_map.iterrows():
    color = 'green' if row['결과'] == '적합' else 'red'
    folium.CircleMarker(
        location=[33.4, 126.5], # ✔ 여기는 실제 지점별 좌표 연동 가능
        radius=8,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        tooltip=f"{row['지점명']} - {row['결과']}"
    ).add_to(m)

st_folium(m, width=1000, height=500)

# 📈 3. 연도별 평균 기온 변화
st.subheader("📈 연도별 평균 기온 변화 (2020~2024)")
df_yearly_temp = df_weather_recent.groupby('연도')['평균기온(°C)'].mean().reset_index()
fig_yearly_temp = px.line(df_yearly_temp, x='연도', y='평균기온(°C)', markers=True)
st.plotly_chart(fig_yearly_temp, use_container_width=True)

st.divider()
st.caption("© 2024 제주 스마트팜 농가 대시보드 | Data: KMA, 농업기술원, 제주특별자치도")

