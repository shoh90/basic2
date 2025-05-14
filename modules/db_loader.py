import pandas as pd
import sqlite3
import streamlit as st

@st.cache_data
def load_data():
    conn = sqlite3.connect('data/asos_weather.db')
    df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
    df_sunshine = pd.read_sql("SELECT * FROM sunshine_data", conn)
    conn.close()

    df_weather['일시'] = pd.to_datetime(df_weather['일시'])
    df_sunshine['일시'] = pd.to_datetime(df_sunshine['일시'])
    return df_weather, df_sunshine
