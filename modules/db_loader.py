import os
import pandas as pd
import sqlite3
import streamlit as st

@st.cache_data
def load_data():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'asos_weather.db')
    db_path = os.path.abspath(db_path)

    if not os.path.exists(db_path):
        st.error(f"❗ DB 파일이 존재하지 않습니다: {db_path}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    conn = sqlite3.connect(db_path)

    # 테이블 목록 확인
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    st.sidebar.success("✅ DB 테이블 목록 확인됨")
    st.sidebar.write(tables)

    # 진짜 테이블명 로딩
    df_weather = pd.read_sql("SELECT * FROM asos_weather", conn) if 'asos_weather' in tables else pd.DataFrame()
    df_sunshine = pd.read_sql("SELECT * FROM sunshine_data", conn) if 'sunshine_data' in tables else pd.DataFrame()
    df_pest_4 = pd.read_sql("SELECT * FROM pest_disease_4", conn) if 'pest_disease_4' in tables else pd.DataFrame()
    df_pest_5 = pd.read_sql("SELECT * FROM pest_disease_5", conn) if 'pest_disease_5' in tables else pd.DataFrame()

    conn.close()

    # 일시 컬럼 변환
    if '일시' in df_weather.columns:
        df_weather['일시'] = pd.to_datetime(df_weather['일시'], errors='coerce')
    if '일시' in df_sunshine.columns:
        df_sunshine['일시'] = pd.to_datetime(df_sunshine['일시'], errors='coerce')

    return df_weather, df_sunshine, df_pest_4, df_pest_5
