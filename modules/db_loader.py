import os
import pandas as pd
import sqlite3
import streamlit as st

@st.cache_data
def load_data():
    # ✅ 절대경로 설정
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'asos_weather.db')
    db_path = os.path.abspath(db_path)

    if not os.path.exists(db_path):
        st.error(f"❗ DB 파일이 존재하지 않습니다: {db_path}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    conn = sqlite3.connect(db_path)

    # ✅ 테이블 목록 확인
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    st.sidebar.success("✅ DB 테이블 목록 확인됨")
    st.sidebar.write(tables)

    # ✅ 필수 테이블 로드 (없으면 에러)
    def load_table(table_name):
        if table_name in tables:
            st.sidebar.write(f"✅ {table_name} 불러옴")
            return pd.read_sql(f"SELECT * FROM {table_name}", conn)
        else:
            st.warning(f"❗ {table_name} 테이블을 찾지 못했습니다.")
            return pd.DataFrame()

    df_weather = load_table('asos_weather')
    df_sunshine = load_table('sunshine_data')
    df_pest_4 = load_table('pest_disease_4')
    df_pest_5 = load_table('pest_disease_5')

    conn.close()

    # ✅ 일시 컬럼 datetime 변환
    if '일시' in df_weather.columns:
        df_weather['일시'] = pd.to_datetime(df_weather['일시'], errors='coerce')
    if '일시' in df_sunshine.columns:
        df_sunshine['일시'] = pd.to_datetime(df_sunshine['일시'], errors='coerce')

    return df_weather, df_sunshine, df_pest_4, df_pest_5
