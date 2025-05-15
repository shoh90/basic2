import streamlit as st
from pages_common import render_chart

st.header("💨 풍속 분석")
render_chart(keyword='풍속', y_label='평균 풍속 (m/s)', title='월별 평균 풍속 추이')
