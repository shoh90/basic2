import streamlit as st
import pandas as pd
import plotly.express as px
from modules.db_loader import load_db_table
from modules.preprocess import preprocess_weather

st.header("🌿 습도 분석")

df_weather = load_db_table('asos_weather')
df_weather = preprocess_weather(df_weather)

st.write("📊 데이터 컬럼명", df_weather.columns)

# 습도 컬럼 자동 탐색
humidity_cols = [col for col in df_weather.columns if '습도' in col]
if humidity_cols:
    col_name = humidity_cols[0]  # 첫 번째 습도 관련 컬럼 사용
    fig = px.line(df_weather, x='일시', y=col_name, title="일별 평균 습도")
    st.plotly_chart(fig)
else:
    st.error("습도 데이터가 없습니다. 컬럼명을 확인하세요.")
