import streamlit as st
import pandas as pd
import plotly.express as px
from modules.db_loader import load_db_table

st.header("💨 바람 분석")

df_weather = load_db_table('asos_weather')
df_weather['일시'] = pd.to_datetime(df_weather['일시'])

fig = px.line(df_weather, x='일시', y='평균 풍속(m/s)', title="일별 평균 풍속")
st.plotly_chart(fig)
