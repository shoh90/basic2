import streamlit as st
from pages_common import render_chart

st.header("🌿 습도 분석")
render_chart(keyword='습도', y_label='평균 습도 (%)', title='월별 평균 습도 추이')
