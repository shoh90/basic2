import streamlit as st
import pandas as pd
import plotly.express as px
from modules.db_loader import load_db_table

st.header("🏠 제주 농부 대시보드 - 전체 요약")

df_weather = load_db_table('asos_weather')
today = df_weather['일시'].max()
today_data = df_weather[df_weather['일시'] == today]

col1, col2, col3 = st.columns(3)
col1.metric("🌡 평균기온(°C)", f"{today_data['평균기온(°C)'].values[0]:.1f}")
col2.metric("🌧 일강수량(mm)", f"{today_data['일강수량(mm)'].values[0]:.1f}")
col3.metric("💨 평균풍속(m/s)", f"{today_data['평균 풍속(m/s)'].values[0]:.1f}")

st.subheader("📅 주간 강수량 예보 (예시)")
dummy = pd.DataFrame({
    '날짜': pd.date_range(start=today, periods=7),
    '예상강수량': [0, 3, 8, 2, 5, 1, 0]
})
fig = px.bar(dummy, x='날짜', y='예상강수량', labels={'예상강수량':'mm'}, title="주간 강수량 예보")
st.plotly_chart(fig)
