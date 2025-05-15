import streamlit as st
from modules.pages_common import render_chart

st.header("🌡 기온 분석")
render_chart(keyword='기온', y_label='평균 기온 (°C)', title='월별 평균 기온 추이')
