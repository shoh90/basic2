import streamlit as st
from modules.db_loader import load_db_table

st.header("🏠 전체 요약 - 오늘의 제주 날씨")

df_weather = load_db_table('asos_weather')
today_data = df_weather[df_weather['일시'] == df_weather['일시'].max()]

col1, col2, col3 = st.columns(3)
col1.metric("🌡 평균기온(°C)", f"{today_data['평균기온(°C)'].values[0]:.1f}")
col2.metric("🌧 일강수량(mm)", f"{today_data['일강수량(mm)'].values[0]:.1f}")
col3.metric("💨 평균풍속(m/s)", f"{today_data['평균 풍속(m/s)'].values[0]:.1f}")

st.subheader("📅 주간 날씨 예보 (예시)")
# 여기서는 실제 예보 데이터가 없으니 임의의 값으로 그래프 표시
import pandas as pd
import plotly.express as px

dummy = pd.DataFrame({
    '날짜': pd.date_range(start='2024-05-13', periods=7),
    '예상기온': [20, 21, 19, 22, 23, 21, 20],
    '예상강수량': [0, 5, 10, 0, 15, 2, 0]
})
fig = px.bar(dummy, x='날짜', y='예상강수량', labels={'예상강수량':'mm'}, title="주간 강수량 예보")
st.plotly_chart(fig)

st.info("오늘은 바람이 강하니 시설물 점검을 추천합니다 🌬️")
