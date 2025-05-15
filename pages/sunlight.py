import streamlit as st
import pandas as pd
import plotly.express as px
from modules.db_loader import load_csv
from modules.preprocess import preprocess_sunshine
from modules.unified_utils import get_column

st.header("🌞 일조량 분석")

# 데이터 로드 & 전처리
df_sun = load_csv('sunshine_data.csv')
df_sun = preprocess_sunshine(df_sun, debug=False)

# '일시' 컬럼에서 '월' 컬럼 생성
if '일시' in df_sun.columns:
    df_sun['월'] = df_sun['일시'].dt.to_period('M').dt.to_timestamp()
else:
    st.error("❗ '일시' 컬럼이 없습니다. 데이터 확인 필요.")
    st.stop()

# '일조시간' 관련 컬럼 자동 탐지
sun_col = get_column(df_sun, ['일조', '일조시간'])
if sun_col is None:
    st.error("❗ '일조시간' 관련 컬럼을 찾지 못했습니다.")
    st.stop()

# 월별 평균 집계
monthly_avg = df_sun.groupby('월')[sun_col].mean().reset_index()

# 게이지 차트 (최근 월 기준)
import plotly.graph_objects as go
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=monthly_avg[sun_col].iloc[-1],
    title={'text': "최근 월평균 일조시간 (hr)"},
    gauge={'axis': {'range': [0, 12]}}
))
st.plotly_chart(fig_gauge)

# 월별 추이 그래프
fig_line = px.line(monthly_avg, x='월', y=sun_col, markers=True,
                   title='월별 평균 일조시간 추이', labels={sun_col: '일조시간 (hr)'})
st.plotly_chart(fig_line)
