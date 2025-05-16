import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="제주 농부 스마트 대시보드", layout="wide", page_icon="🍊")

st.title("🍊 제주 농부 스마트 대시보드")
st.markdown("제주 농사에 필요한 모든 기능을 통합하여 제공합니다. 좌측 메뉴 또는 아래에서 원하는 항목을 선택하세요.")

# 대시보드 주요 기능 안내 카드
col1, col2, col3 = st.columns(3)
with col1:
    st.header("📡 실시간 기후 모니터링")
    st.write("오늘의 날씨, 주간 예보, 이상기후 경고")
    st.page_link("pages/실시간 기후 모니터링 및 이상 기후 알림.py", label="실시간 기후 ➡️")

with col2:
    st.header("🍊 감귤 재배 적합지 추천")
    st.write("월별 감귤 재배 적합도 지도 및 추천 지역")
    st.page_link("pages/감귤 재배 적합지 추천.py", label="적합지 추천 ➡️")

with col3:
    st.header("🐛 병해충 방제약 및 분석")
    st.write("병해충 발생 시기, 위험도 분석, 방제약 안내")
    st.page_link("pages/병해충 분석.py", label="병해충 분석 ➡️")

# 추가 페이지가 있을 경우 여기에 계속 추가 가능
# 예:
# st.page_link("pages/일조량 분석.py", label="일조량 분석 ➡️")

# 푸터
st.divider()
st.caption("© 2024 제주 스마트팜 농가 대시보드 | Data: KMA, 농업기술원, 제주특별자치도")
