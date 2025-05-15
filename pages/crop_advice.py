import streamlit as st
import pandas as pd

st.header("🥕 작물 맞춤 조언")

advice_data = {
    "감귤": "5월에는 꽃이 지고 열매가 맺히는 시기입니다. 물관리를 철저히 하고 병해충 주의하세요.",
    "배추": "벌레가 많아지는 시기입니다. 잡초 제거와 병충해 방제를 추천합니다.",
    "브로콜리": "고온다습한 날씨에 뿌리썩음병이 발생할 수 있으니 배수관리에 신경쓰세요."
}

crop = st.selectbox("작물을 선택하세요", list(advice_data.keys()))
st.info(advice_data[crop])
