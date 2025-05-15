import pandas as pd
import sqlite3
import streamlit as st

@st.cache_data
def load_data():
    # DB 파일 경로는 고정: data/asos_weather.db
    conn = sqlite3.connect('data/asos_weather.db')

    # asos_weather 테이블
    df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
    # sunshine_data 테이블
    df_sunshine = pd.read_sql("SELECT * FROM sunshine_data", conn)
    # pest_disease_4 테이블 (제주시 데이터)
    df_pest_4 = pd.read_sql("SELECT * FROM pest_disease_4", conn)
    # pest_disease_5 테이블 (서귀포시 데이터)
    df_pest_5 = pd.read_sql("SELECT * FROM pest_disease_5", conn)

    conn.close()

    # 일시 컬럼은 datetime 형식으로 변환
    if '일시' in df_weather.columns:
        df_weather['일시'] = pd.to_datetime(df_weather['일시'], errors='coerce')
    if '일시' in df_sunshine.columns:
        df_sunshine['일시'] = pd.to_datetime(df_sunshine['일시'], errors='coerce')

    return df_weather, df_sunshine, df_pest_4, df_pest_5
