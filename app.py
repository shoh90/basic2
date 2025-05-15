import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="제주 농부 스마트 대시보드",
    layout="wide",
    page_icon="🍊"
)

# ----------------- 상단 대시보드 소개 -----------------
st.title("🍊 제주 농부 스마트 대시보드")

st.markdown("""
제주도 농사에 필요한 모든 정보를 한 곳에서 확인하세요.  
왼쪽 메뉴에서 원하는 항목을 선택하세요.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🏠 전체 요약")
    st.markdown("오늘 날씨 / 주간 예보 / 감귤 재배량 지도")

with col2:
    st.subheader("📊 기후 & 병해충 분석")
    st.markdown("기온 / 강수량 / 풍속 / 습도 / 일조량 / 병해충 분석")

with col3:
    st.subheader("🥕 작물 맞춤 조언")
    st.markdown("감귤, 배추 등 월별 맞춤형 농업 조언 제공")

st.divider()
st.caption("© 2024 제주 스마트팜 농가 대시보드 | Data: KMA, 제주특별자치도")

# ----------------- 아래 감귤 재배 적합도 지도 -----------------
st.subheader("📍 제주 감귤 재배 적합도 종합 지도 (월별)")

# ✅ 월 선택
month = st.selectbox("확인할 월을 선택하세요", list(range(1, 13)))

# ✅ 샘플 데이터 (여기선 간단히 가상데이터)
data = {
    '읍면동': ['한림읍', '애월읍', '성산읍', '남원읍'],
    '적합도': [0.85, 0.65, 0.72, 0.5],
    '재배량(톤)': [3000, 2500, 1500, 1800],
    '위도': [33.41, 33.45, 33.38, 33.25],
    '경도': [126.26, 126.32, 126.91, 126.68]
}
df = pd.DataFrame(data)
df['결과'] = df['적합도'].apply(lambda x: '적합' if x >= 0.7 else '부적합')

# ✅ Folium 지도 생성
m = folium.Map(location=[33.4, 126.5], zoom_start=10)

for idx, row in df.iterrows():
    color = 'green' if row['결과'] == '적합' else 'red'
    folium.CircleMarker(
        location=[row['위도'], row['경도']],
        radius=10,
        color=color,
        fill=True,
        fill_opacity=0.6,
        popup=f"{row['읍면동']}\n재배량: {row['재배량(톤)']}톤\n적합도: {row['적합도']:.2f}",
        tooltip=row['결과']
    ).add_to(m)

# ✅ 지도 표시
st_folium(m, width=1000, height=600)
