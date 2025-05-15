import streamlit as st
import pandas as pd
import plotly.express as px
from modules.db_loader import load_db_table
from modules.preprocess import preprocess_weather

st.header("🌿 습도 분석")

df_weather = load_db_table('asos_weather')
df_weather = preprocess_weather(df_weather)

# st.write("📊 데이터 컬럼명", df_weather.columns)  # 숨김

# 습도 컬럼 자동 탐색
humidity_cols = [col for col in df_weather.columns if '습도' in col]
if humidity_cols:
    col_name = humidity_cols[0]  # 첫 번째 습도 컬럼 사용

    # 월별 평균으로 그룹화 (보기 좋게)
    df_weather['월'] = df_weather['일시'].dt.to_period('M').dt.to_timestamp()
    monthly_avg = df_weather.groupby('월')[col_name].mean().reset_index()

    fig = px.line(monthly_avg, x='월', y=col_name,
                  markers=True,
                  title="월별 평균 습도 추이",
                  labels={col_name: '평균 습도 (%)'})

    fig.update_layout(yaxis_range=[0, 100], xaxis_title='날짜')
    st.plotly_chart(fig)
else:
    st.error("습도 데이터가 없습니다. 컬럼명을 확인하세요.")
