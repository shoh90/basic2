import streamlit as st
import pandas as pd
import plotly.express as px
from modules.db_loader import load_db_table

st.header("🌧 강수량 분석")

df_weather = load_db_table('asos_weather')
df_weather['일시'] = pd.to_datetime(df_weather['일시'])

fig = px.bar(df_weather, x='일시', y='일강수량(mm)', title="일별 강수량 누적")
st.plotly_chart(fig)
