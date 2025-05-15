import streamlit as st
import pandas as pd
import plotly.express as px
from modules.db_loader import load_db_table
from modules.preprocess import preprocess_weather

def render_chart(keyword, y_label, title):
    df_weather = load_db_table('asos_weather')
    df_weather = preprocess_weather(df_weather)

    # 1. 컬럼 자동 탐색
    target_cols = [col for col in df_weather.columns if keyword in col]
    if not target_cols:
        st.error(f"⚠️ '{keyword}'가 포함된 컬럼이 없습니다. 데이터 확인 필요.")
        return

    col_name = target_cols[0]
    st.info(f"📊 기준 컬럼: {col_name}")

    # 2. 월별 평균으로 집계
    df_weather['월'] = df_weather['일시'].dt.to_period('M').dt.to_timestamp()
    monthly_avg = df_weather.groupby('월')[col_name].mean().reset_index()

    # 3. 그래프 그리기
    fig = px.line(monthly_avg, x='월', y=col_name, markers=True,
                  title=title, labels={col_name: y_label})

    fig.update_layout(yaxis_range=[0, None], xaxis_title='날짜')
    st.plotly_chart(fig)
