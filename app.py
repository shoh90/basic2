import streamlit as st

# ✅ 페이지 설정 (제목, 레이아웃, 아이콘)
st.set_page_config(
    page_title="제주 농부 스마트 대시보드",
    layout="wide",
    page_icon="🍊"
)

# ✅ 대시보드 메인 타이틀
st.title("🍊 제주 농부 스마트 대시보드")

st.markdown("""
제주도 농사에 필요한 모든 정보를 한 곳에서 확인하세요.  
왼쪽 메뉴 또는 아래 카드에서 원하는 항목을 클릭하세요.
""")

# ✅ 카드형 링크 (3개 컬럼 레이아웃)
col1, col2, col3 = st.columns(3)

# 🏠 전체 요약
with col1:
    st.subheader("🏠 전체 요약")
    st.markdown("""
    - 오늘 날씨
    - 주간 예보
    - 감귤 재배량 지도
    """)
    st.page_link("1_main_overview", label="바로가기 ➡️")

# 📊 기후 & 병해충 분석
with col2:
    st.subheader("📊 기후 & 병해충 분석")
    st.markdown("""
    - 기온, 강수량, 풍속, 습도, 일조량
    - 병해충 발생 현황 및 경고
    """)
    st.page_link("2_temperature", label="기온 분석 ➡️")
    st.page_link("2_pest_disease", label="병해충 분석 ➡️")

# 🥕 작물 맞춤 조언
with col3:
    st.subheader("🥕 작물 맞춤 조언")
    st.markdown("""
    - 감귤, 배추 등 월별 재배 관리법
    - 실질적인 농업 조언 제공
    """)
    st.page_link("3_crop_advice", label="작물 조언 ➡️")

# ✅ 하단 구분선 & Footer
st.divider()
st.caption("© 2024 제주 스마트팜 농가 대시보드 | Data: KMA, 제주도청, 농업기술원")
