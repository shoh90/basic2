import streamlit as st

st.set_page_config(
    page_title="제주 농부 스마트 대시보드",
    layout="wide",
    page_icon="🍊"
)

st.title("🍊 제주 농부 스마트 대시보드")

st.markdown("""
제주도 농사에 필요한 모든 정보를 한 곳에서 확인하세요.  
왼쪽 메뉴 또는 아래 카드에서 원하는 항목을 클릭하세요.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🏠 전체 요약")
    st.markdown("오늘 날씨, 주간 예보, 감귤 재배량 지도를 한 번에 확인")
    st.page_link("pages/1_main_overview.py", label="바로가기 ➡️")

with col2:
    st.subheader("📊 기후 & 병해충 분석")
    st.markdown("- 기온, 강수량, 풍속, 습도, 일조량\n- 병해충 발생 현황 및 경고")
    st.page_link("2_temperature", label="기온 분석 ➡️")
    st.page_link("2_pest_disease", label="병해충 분석 ➡️")

with col3:
    st.subheader("🥕 작물 맞춤 조언")
    st.markdown("감귤, 배추 등 월별 재배 관리법 제공")
    st.page_link("pages/3_crop_advice.py", label="작물 조언 ➡️")

st.divider()
st.caption("© 2024 제주 스마트팜 농가 대시보드 | Data: KMA, 제주도청, 농업기술원")
