import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.db_loader import load_csv

st.header("🌞 일조량 분석")

df_sun = load_csv('sunshine_data.csv')
df_sun['일시'] = pd.to_datetime(df_sun['일시'])

latest = df_sun['일시'].max()
latest_data = df_sun[df_sun['일시'] == latest]

fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=latest_data['일조시간(hr)'].values[0],
    title={'text': "일조시간 (hr)"},
    gauge={'axis': {'range': [0, 12]}}
))
st.plotly_chart(fig)
