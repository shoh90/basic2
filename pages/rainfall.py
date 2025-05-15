import streamlit as st
from modules.pages_common import render_chart

st.header("🌧 강수량 분석")
render_chart(keyword='강수량', y_label='일강수량 (mm)', title='월별 평균 강수량 추이')
