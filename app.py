import streamlit as st

st.set_page_config(page_title="제주 농부 스마트 대시보드", layout="wide", page_icon="🍊")

st.title("🍊 제주 농부 스마트 대시보드")
st.markdown("제주 농사에 필요한 모든 기능을 통합하여 제공합니다.\n좌측 메뉴 또는 아래 카드에서 원하는 기능을 선택하세요.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📡 실시간 기후 모니터링")
    st.page_link("pages/1_실시간 기후 모니터링 및 이상 기후 알림.py", label="실시간 기후 ➡️")

    st.subheader("🍊 감귤 재배 적합지 추천")
    st.page_link("pages/1_감귤 재배 적합지 추천.py", label="적합지 추천 ➡️")

    st.subheader("📅 감귤 생육 체크리스트")
    st.page_link("pages/3_월별 감귤 생육 체크리스트.py", label="체크리스트 ➡️")

with col2:
    st.subheader("🌧 기후 & 병해충 분석")
    st.page_link("pages/2_기온 분석.py", label="기온 분석 ➡️")
    st.page_link("pages/2_강수량 분석.py", label="강수량 분석 ➡️")
    st.page_link("pages/2_습도 분석.py", label="습도 분석 ➡️")
    st.page_link("pages/2_일조량 분석.py", label="일조량 분석 ➡️")
    st.page_link("pages/2_풍속 분석.py", label="풍속 분석 ➡️")
    st.page_link("pages/2_병해충 발생 알림.py", label="병해충 발생 ➡️")

    st.subheader("📰 뉴스 & 정책 안내")
    st.page_link("pages/4_감귤 관련 뉴스 및 정책 정보 안내.py", label="뉴스 & 정책 ➡️")

st.divider()
st.caption("© 2024 제주 스마트팜 농가 대시보드 | Data: KMA, 농업기술원, 제주특별자치도")
