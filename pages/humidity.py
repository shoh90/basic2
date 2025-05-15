import streamlit as st
import pandas as pd
import plotly.express as px
from modules.db_loader import load_db_table
from modules.preprocess import preprocess_weather

st.header("🌿 습도 분석")

df_weather = load_db_table('asos_weather')
df_weather = preprocess_weather(df_weather)

st.write("📊 데이터 확인용", df_weather.columns)

# 여기서 컬럼명을 정확히 확인하세요 (ex: '평균상대습도(%)'인지 '평균 상대습도(%)'인지)
col_name = '평균상대습도(%)' if '평균상대습도(%)' in df_weather.columns else '평균 상대습도(%)'

fig = px.line(df_weather, x='일시', y=col_name, title="일별 평균 습도")
st.plotly_chart(fig)
