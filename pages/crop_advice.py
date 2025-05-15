import streamlit as st

st.header("🥕 작물 맞춤 조언")

advice_data = {
    "감귤": "5월에는 꽃이 지고 열매가 맺히는 시기입니다. 물 관리와 병해충 주의가 필요합니다.",
    "배추": "벌레가 많아지는 시기입니다. 잡초 제거 및 방제를 추천합니다.",
    "브로콜리": "고온다습한 날씨에 뿌리썩음병 주의! 배수관리가 중요합니다."
}

crop = st.selectbox("작물을 선택하세요", list(advice_data.keys()))
st.info(advice_data[crop])
