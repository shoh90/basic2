import os
import pandas as pd
import sqlite3

@st.cache_data
def load_db_table(table_name):
    db_path = os.path.join('data', 'asos_weather.db')
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

@st.cache_data
def load_csv(file_name):
    csv_path = os.path.join('data', file_name)
    return pd.read_csv(csv_path)
