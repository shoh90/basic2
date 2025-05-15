import streamlit as st
import pandas as pd
import plotly.express as px
from modules.db_loader import load_db_table

st.header("🌿 습도 분석")

df_weather = load_db_table('asos_weather')
df_weather['일시'] = pd.to_datetime(df_weather['일시'])

fig = px.line(df_weather, x='일시', y='평균 상대습도(%)', title="일별 평균 습도")
st.plotly_chart(fig)
