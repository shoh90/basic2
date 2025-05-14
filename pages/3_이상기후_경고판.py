import streamlit as st
import pandas as pd
from modules.load_data import load_data
import plotly.express as px

st.title("🌪️ 이상기후 + 병해충 경고판")

# 데이터 로딩
df_weather, _ = load_data()

# 연월 컬럼 추가
df_weather['연월'] = df_weather['일시'].dt.to_period('M').astype(str)

# ✅ 이상기후 기준
df_weather['연속무강수'] = df_weather['일강수량(mm)'].rolling(5).apply(lambda x: (x == 0).sum(), raw=True)
df_weather['고온경고'] = df_weather['평균기온(°C)'] >= 30
df_weather['강풍경고'] = df_weather['평균풍속(m/s)'] >= 5

# ✅ 병해충 경고 (예시 기준)
# 기준1: 평균기온 25도 이상 + 평균습도 80% 이상 (곰팡이성 병해충 위험)
df_weather['병해충_곰팡이'] = (df_weather['평균기온(°C)'] >= 25) & (df_weather['평균상대습도(%)'] >= 80)

# 기준2: 평균기온 20도 이상 + 무강수 7일 이상 (진딧물/응애류 위험)
df_weather['병해충_해충'] = (df_weather['평균기온(°C)'] >= 20) & (df_weather['연속무강수'] >= 7)

# ✅ 이상기후+병해충 종합 경고 필터
alerts_df = df_weather[
    (df_weather['연속무강수'] >= 5) |
    (df_weather['고온경고']) |
    (df_weather['강풍경고']) |
    (df_weather['병해충_곰팡이']) |
    (df_weather['병해충_해충'])
]

# 📊 경고 현황 테이블
st.subheader("⚠️ 경고 발생 현황")
st.dataframe(alerts_df[['일시', '지점명', '평균기온(°C)', '평균상대습도(%)', '일강수량(mm)', '평균풍속(m/s)',
                        '연속무강수', '고온경고', '강풍경고', '병해충_곰팡이', '병해충_해충']])

# 📊 월별 병해충 경고 추이 (집계 시각화)
st.subheader("🦠 병해충 경고 월별 추이")

df_monthly = alerts_df.groupby(['연월']).agg({
    '병해충_곰팡이': 'sum',
    '병해충_해충': 'sum'
}).reset_index()

fig = px.bar(df_monthly, x='연월', y=['병해충_곰팡이', '병해충_해충'],
             title='월별 병해충 경고 건수', barmode='group')
st.plotly_chart(fig, use_container_width=True)
