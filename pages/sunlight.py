import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.db_loader import load_csv
from modules.preprocess import preprocess_sunshine

st.header("🌞 일조량 분석")

df_sun = load_csv('sunshine_data.csv')
df_sun = preprocess_sunshine(df_sun)

df_sun['월'] = df_sun['일시'].dt.to_period('M').dt.to_timestamp()
monthly_avg = df_sun.groupby('월')['일조시간(hr)'].mean().reset_index()

fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=monthly_avg['일조시간(hr)'].iloc[-1],
    title={'text': "최근 월평균 일조시간 (hr)"},
    gauge={'axis': {'range': [0, 12]}}
))
st.plotly_chart(fig)

# 선그래프도 같이 보기
import plotly.express as px
fig2 = px.line(monthly_avg, x='월', y='일조시간(hr)', markers=True,
               title='월별 평균 일조시간 추이', labels={'일조시간(hr)': '일조시간 (hr)'})
st.plotly_chart(fig2)
