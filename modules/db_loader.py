import os
import pandas as pd
import sqlite3
import streamlit as st  # ✅ 이거 빠져서 오류난 거에요!

@st.cache_data
def load_db_table(table_name):
    db_path = os.path.join('data', 'asos_weather.db')
    if not os.path.exists(db_path):
        st.error(f"DB 파일이 존재하지 않습니다: {db_path}")
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

@st.cache_data
def load_csv(file_name):
    csv_path = os.path.join('data', file_name)
    if not os.path.exists(csv_path):
        st.error(f"CSV 파일이 존재하지 않습니다: {csv_path}")
        return pd.DataFrame()
    return pd.read_csv(csv_path)
