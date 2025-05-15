import os
import pandas as pd
import sqlite3
import streamlit as st

@st.cache_data
def load_data():
    # ✅ 1. 안전한 절대경로로 DB 연결
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'asos_weather.db')
    db_path = os.path.abspath(db_path)

    if not os.path.exists(db_path):
        st.error(f"❗ DB 파일이 존재하지 않습니다: {db_path}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    conn = sqlite3.connect(db_path)

    # ✅ 2. 실제 테이블 목록 확인
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    st.sidebar.success("✅ DB 테이블 목록 확인됨")
    st.sidebar.write(tables)

    # ✅ 3. 테이블 매핑 함수 (유사 이름 찾아서 매칭)
    def find_table(expected_name):
        for table in tables:
            if expected_name.lower() in table.lower():
                return table
        st.warning(f"❗ '{expected_name}'와 유사한 테이블을 찾지 못했습니다.")
        return None

    table_weather = find_table('asos_weather')
    table_sunshine = find_table('sunshine_data')
    table_pest_4 = find_table('pest_disease_4')
    table_pest_5 = find_table('pest_disease_5')

    # ✅ 4. 데이터 로딩 (없으면 빈 DataFrame 반환)
    def safe_read_sql(table_name):
        if table_name:
            return pd.read_sql(f"SELECT * FROM {table_name}", conn)
        else:
            return pd.DataFrame()

    df_weather = safe_read_sql(table_weather)
    df_sunshine = safe_read_sql(table_sunshine)
    df_pest_4 = safe_read_sql(table_pest_4)
    df_pest_5 = safe_read_sql(table_pest_5)

    conn.close()

    # ✅ 5. 날짜형 컬럼 처리
    if '일시' in df_weather.columns:
        df_weather['일시'] = pd.to_datetime(df_weather['일시'], errors='coerce')
    if '일시' in df_sunshine.columns:
        df_sunshine['일시'] = pd.to_datetime(df_sunshine['일시'], errors='coerce')

    return df_weather, df_sunshine, df_pest_4, df_pest_5
