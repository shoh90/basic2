import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import altair as alt # altair 차트 사용 예시

# 페이지 기본 설정
st.set_page_config(page_title="제주 농부 스마트 대시보드", layout="wide", page_icon="🍊")

st.title("🍊 제주 농부 스마트 대시보드")
st.markdown("제주 농사에 필요한 모든 기능을 통합하여 제공합니다. 아래에서 원하는 정보를 확인하세요.")
st.markdown("---")

# ========================================
# 1. 실시간 기후 모니터링 및 이상 기후 알림
# ========================================
def display_realtime_weather():
    st.header("📡 실시간 기후 모니터링 및 이상 기후 알림")
    # st.write("오늘의 날씨, 주간 예보, 이상기후 경고 등을 제공합니다.") # 헤더에서 이미 설명

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("오늘의 날씨 (제주시)")
        st.metric(label="기온", value="25 °C", delta="1.2 °C")
        st.write("☀️ 맑음")
        st.write("💧 습도: 60%")
        st.write("🌬️ 풍속: 3m/s")

    with col2:
        st.subheader("주간 예보 (제주시)")
        forecast_data = pd.DataFrame({
            '요일': ['월', '화', '수', '목', '금', '토', '일'],
            '날씨': ['☀️', '☁️', '🌧️', '☀️', '🌥️', '☀️', '🌦️'],
            '최고(°C)': [26, 27, 24, 28, 25, 29, 23],
            '최저(°C)': [18, 19, 17, 20, 18, 21, 16]
        })
        st.dataframe(forecast_data.set_index('요일'), height=280) # 높이 조절

    with col3:
        st.subheader("이상 기후 알림")
        alert_on = st.toggle("가상 이상 기후 발생 (폭염 주의보)", value=False)
        if alert_on:
            st.warning("🚨 **주의:** 현재 폭염 주의보가 발령되었습니다. 농작물 관리에 각별히 유의하시기 바랍니다.")
        else:
            st.success("✅ 현재 특별한 이상 기후 알림은 없습니다.")
        st.markdown("_(실제 데이터 연동 시 자동 업데이트)_")

    st.markdown("---")

# ========================================
# 2. 감귤 재배 적합지 추천
# ========================================
def display_citrus_suitability():
    st.header("🍊 감귤 재배 적합지 추천")
    # st.write("월별 감귤 재배 적합도 지도 및 추천 지역 정보를 제공합니다.")

    col1, col2 = st.columns([2,1]) # 지도에 더 많은 공간 할애
    with col1:
        st.subheader("감귤 재배 적합도 지도")
        # 제주도 중심 좌표 근처의 임의의 점들
        map_data = pd.DataFrame(
            np.random.randn(100, 2) / [15, 15] + [33.3617, 126.5292], # 제주도청 근처
            columns=['lat', 'lon'])
        map_data['적합도'] = np.random.rand(100) * 100 # 0~100 사이의 임의 적합도
        
        # Altair를 사용한 지도 위 점 시각화 (간단 예시)
        # 실제로는 Folium, Pydeck 등을 사용하는 것이 더 효과적입니다.
        # 여기서는 st.map으로 대체합니다. 더미 데이터이므로 색상 구분은 생략.
        st.map(map_data, latitude='lat', longitude='lon', size='적합도', color='#FFA500', zoom=8)
        st.caption("지도 위의 점 크기는 임의의 '적합도'를 나타냅니다 (예시).")

    with col2:
        st.subheader("추천 지역 Top 3")
        st.markdown("""
        1.  **서귀포시 남원읍:**
            *   일조량: 매우 우수
            *   평균 기온: 적정
            *   강수량: 양호
        2.  **제주시 한경면:**
            *   일조량: 우수
            *   평균 기온: 적정
            *   토양: 배수 양호
        3.  **서귀포시 안덕면:**
            *   일조량: 양호
            *   평균 기온: 약간 높음
            *   병해충: 관리 용이
        """)
    st.markdown("---")

# ========================================
# 3. 병해충 발생 알림 및 분석
# ========================================
def display_pest_analysis():
    st.header("🐛 병해충 발생 알림 및 분석")
    # st.write("병해충 발생 시기, 위험도 분석, 방제약 안내 등을 제공합니다.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("주요 병해충 발생 위험도 (예시)")
        pest_data = pd.DataFrame({
            '병해충': ['귤응애', '진딧물', '총채벌레', '더뎅이병', '검은점무늬병'],
            '현재 위험도': ['주의', '경계', '관심', '주의', '관심'],
            '예상 발생 피크': ['7-8월', '5-6월', '6-7월', '장마철', '9-10월']
        })
        st.dataframe(pest_data.set_index('병해충'))

    with col2:
        st.subheader("병해충 발생 예측 (귤응애 예시)")
        chart_data = pd.DataFrame({
            '월': pd.to_datetime([f'2024-{m:02d}-01' for m in range(4, 11)]),
            '예상 밀도 (마리/잎)': [5, 15, 30, 45, 35, 20, 10]
        })
        c = alt.Chart(chart_data).mark_area(
            line={'color':'darkgreen'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='white', offset=0),
                       alt.GradientStop(color='lightgreen', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X('월:T', title='월', axis=alt.Axis(format='%m월')),
            y=alt.Y('예상 밀도 (마리/잎):Q', title='예상 밀도'),
            tooltip=['월:T', '예상 밀도 (마리/잎):Q']
        ).properties(
            title='귤응애 월별 예상 밀도'
        )
        st.altair_chart(c, use_container_width=True)

    st.subheader("추천 방제약 (예시)")
    st.info("""
    - **귤응애:** 아바멕틴 유제, 스피로메시펜 액상수화제
    - **진딧물:** 이미다클로프리드 수화제, 아세타미프리드 수화제
    - _**주의:** 농약 사용 전 반드시 농약안전정보시스템(psis.rda.go.kr)에서 사용 지침을 확인하세요._
    """)
    st.markdown("---")

# ========================================
# 4. 기후 상세 분석 (탭으로 구성)
# ========================================
def display_climate_analysis():
    st.header("📊 기후 상세 분석")

    tab_titles = ["강수량", "기온", "습도", "일조량", "풍속"]
    tabs = st.tabs(tab_titles)

    # 예시 데이터 생성 함수
    def create_monthly_data(seed_offset=0):
        np.random.seed(42 + seed_offset)
        months = pd.to_datetime([f'2023-{m:02d}-01' for m in range(1, 13)])
        return months

    with tabs[0]: # 강수량 분석
        st.subheader("💧 강수량 분석")
        months = create_monthly_data(0)
        precipitation = np.random.randint(50, 400, size=12)
        prec_data = pd.DataFrame({'월': months, '강수량(mm)': precipitation})
        
        c_prec = alt.Chart(prec_data).mark_bar().encode(
            x=alt.X('월:T', title='월', axis=alt.Axis(format='%m월')),
            y=alt.Y('강수량(mm):Q', title='강수량 (mm)'),
            tooltip=['월:T', '강수량(mm):Q']
        ).properties(title='월별 평균 강수량 (작년 예시)')
        st.altair_chart(c_prec, use_container_width=True)
        st.metric("최근 7일 누적 강수량", "25 mm", "5 mm (전주 대비)")

    with tabs[1]: # 기온 분석
        st.subheader("🌡️ 기온 분석")
        months = create_monthly_data(1)
        avg_temp = np.random.uniform(5, 28, size=12)
        max_temp = avg_temp + np.random.uniform(2, 5, size=12)
        min_temp = avg_temp - np.random.uniform(2, 5, size=12)
        temp_data = pd.DataFrame({'월': months, '평균기온': avg_temp, '최고기온': max_temp, '최저기온': min_temp})
        temp_data_melted = temp_data.melt('월', var_name='구분', value_name='기온(°C)')

        c_temp = alt.Chart(temp_data_melted).mark_line(point=True).encode(
            x=alt.X('월:T', title='월', axis=alt.Axis(format='%m월')),
            y=alt.Y('기온(°C):Q', title='기온 (°C)'),
            color='구분:N',
            strokeDash='구분:N', # 점선 등으로 구분
            tooltip=['월:T', '구분:N', '기온(°C):Q']
        ).properties(title='월별 평균/최고/최저 기온 (작년 예시)')
        st.altair_chart(c_temp, use_container_width=True)

    with tabs[2]: # 습도 분석
        st.subheader("💦 습도 분석")
        months = create_monthly_data(2)
        humidity = np.random.randint(60, 85, size=12)
        hum_data = pd.DataFrame({'월': months, '평균습도(%)': humidity})

        c_hum = alt.Chart(hum_data).mark_line(point=True, color='teal').encode(
            x=alt.X('월:T', title='월', axis=alt.Axis(format='%m월')),
            y=alt.Y('평균습도(%):Q', title='평균 습도 (%)', scale=alt.Scale(domain=[0, 100])),
            tooltip=['월:T', '평균습도(%):Q']
        ).properties(title='월별 평균 습도 (작년 예시)')
        st.altair_chart(c_hum, use_container_width=True)
        st.metric("현재 습도", "65 %", "-3 % (어제 동일 시간 대비)")


    with tabs[3]: # 일조량 분석
        st.subheader("☀️ 일조량 분석")
        months = create_monthly_data(3)
        sunshine_hours = np.random.randint(100, 250, size=12)
        sun_data = pd.DataFrame({'월': months, '일조시간(hr)': sunshine_hours})

        c_sun = alt.Chart(sun_data).mark_bar(color='orange').encode(
            x=alt.X('월:T', title='월', axis=alt.Axis(format='%m월')),
            y=alt.Y('일조시간(hr):Q', title='일조시간 (hr)'),
            tooltip=['월:T', '일조시간(hr):Q']
        ).properties(title='월별 누적 일조시간 (작년 예시)')
        st.altair_chart(c_sun, use_container_width=True)
        st.metric("금일 누적 일조시간", "5.2 시간", "0.5 시간 (어제 대비)")

    with tabs[4]: # 풍속 분석
        st.subheader("🌬️ 풍속 분석")
        months = create_monthly_data(4)
        wind_speed = np.random.uniform(1.5, 4.5, size=12)
        wind_data = pd.DataFrame({'월': months, '평균풍속(m/s)': wind_speed})

        c_wind = alt.Chart(wind_data).mark_line(point=True, color='grey').encode(
            x=alt.X('월:T', title='월', axis=alt.Axis(format='%m월')),
            y=alt.Y('평균풍속(m/s):Q', title='평균 풍속 (m/s)'),
            tooltip=['월:T', '평균풍속(m/s):Q']
        ).properties(title='월별 평균 풍속 (작년 예시)')
        st.altair_chart(c_wind, use_container_width=True)
        st.metric("현재 풍속", "2.1 m/s", "북서풍")
    st.markdown("---")


# ========================================
# 5. 월별 감귤 생육 체크리스트
# ========================================
def display_monthly_checklist():
    st.header("🗓️ 월별 감귤 생육 체크리스트")
    
    # 현재 월을 기준으로 selectbox 기본값 설정
    current_month_index = pd.Timestamp.now().month - 1
    month_names = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월']
    
    selected_month = st.selectbox("확인할 월을 선택하세요:", options=month_names, index=current_month_index)

    checklists = {
        '1월': ["- 동해 예방: 주간부 피복, 방풍망 점검", "- 전정 준비: 전정 도구 정비, 전정 계획 수립", "- 과원 정리: 병든 가지 제거, 낙엽 정리"],
        '2월': ["- 전정 실시: 수세 안정 및 결실 관리 중점", "- 밑거름 시비: 유기질 비료 및 토양개량제 살포", "- 관수시설 점검"],
        '3월': ["- 봄 비료 시비 (1차 웃거름)", "- 새순 관리: 너무 많은 새순 솎아주기", "- 수분 관리: 건조 시 관수"],
        '4월': ["- 개화 전 병해충 방제: 잿빛곰팡이병, 응애류 등", "- 인공수분 준비 (필요시)", "- 잡초 관리 시작"],
        '5월': ["- 개화기 관리: 안정적인 수정 유도", "- 1차 생리낙과 후 적과 준비", "- 병해충 관찰 강화: 진딧물, 총채벌레 등"],
        '6월': ["- 1차 적과 실시: 소과, 기형과, 병해충과 제거", "- 여름 비료 시비 (2차 웃거름)", "- 장마 대비: 배수로 정비, 습해 예방"],
        '7월': ["- 2차 적과 (마무리 적과): 품질 향상 목적", "- 여름 전정: 도장지, 밀생가지 제거", "- 병해충 집중 방제: 깍지벌레, 귤굴나방 등"],
        '8월': ["- 고온기 수분 관리: 토양 수분 유지", "- 칼슘제 엽면시비 (열과 예방)", "- 태풍 대비: 지주시설 점검, 가지 보호"],
        '9월': ["- 가을 비료 시비 (3차 웃거름, 수확 후 감사비료와 구분)", "- 착색 증진 관리: 반사필름 설치 (필요시)", "- 조생종 수확 준비"],
        '10월': ["- 조생종 감귤 수확 및 선별", "- 수확 후 과원 관리", "- 병해충 예찰 지속"],
        '11월': ["- 중생종 감귤 수확", "- 저장 감귤 관리: 예조, 저장고 환경 점검", "- 월동 병해충 방제 준비"],
        '12월': ["- 만생종 감귤 수확 (일부)", "- 감사 비료 시비 (수확 후)", "- 동해 방지 작업 마무리"]
    }
    if selected_month in checklists:
        st.markdown(f"#### {selected_month} 주요 농작업")
        for item in checklists[selected_month]:
            st.checkbox(item, value=False, key=f"{selected_month}_{item}") # key를 고유하게
    else:
        st.info(f"{selected_month}의 체크리스트가 아직 준비되지 않았습니다.")
    st.markdown("---")

# ========================================
# 6. 감귤 관련 뉴스 및 정책 정보 안내
# ========================================
def display_citrus_news_policy():
    st.header("📰 감귤 관련 뉴스 및 정책 정보 안내")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("최신 뉴스")
        news_items = {
            "제주 감귤, 올해 작황 '양호'...당도 기대": "https://example.com/news1",
            "스마트팜 기술 도입, 감귤 농가 생산성 향상": "https://example.com/news2",
            "기후변화 대응 위한 감귤 신품종 개발 박차": "https://example.com/news3",
            "제주 농업기술원, 병해충 예방 교육 실시": "https://example.com/news4"
        }
        for title, url in news_items.items():
            st.markdown(f"- [{title}]({url})")

    with col2:
        st.subheader("주요 지원 정책")
        policy_items = {
            "청년농업인 영농정착 지원사업": "농림축산식품부",
            "밭작물 공동경영체 육성지원": "제주특별자치도",
            "농기계 임대사업 확대": "각 지역 농업기술센터",
            "친환경농업 직불금": "국립농산물품질관리원"
        }
        for title, agency in policy_items.items():
            st.markdown(f"- **{title}**: {agency}")
    st.markdown("_(실제 뉴스/정책은 크롤링 또는 API를 통해 최신 정보로 업데이트 필요)_")
    st.markdown("---")


# ========================================
# 메인 대시보드 레이아웃 구성
# ========================================

# 섹션 1: 실시간 정보 (기후, 병해충)
with st.container(border=True):
    display_realtime_weather()

with st.container(border=True):
    display_pest_analysis()


# 섹션 2: 분석 정보 (적합지, 기후 상세)
with st.expander("📍 감귤 재배 적합지 추천 (상세)", expanded=False):
    display_citrus_suitability()

with st.expander("📊 기후 상세 분석 (강수량, 기온, 습도, 일조량, 풍속)", expanded=True):
    display_climate_analysis()


# 섹션 3: 농업 관리 및 정보
with st.container(border=True):
    display_monthly_checklist()

with st.container(border=True):
    display_citrus_news_policy()


# 푸터
st.divider()
st.caption("© 2024 제주 농부 스마트 대시보드 | Data Sources: KMA (가상), 농업기술원 (가상), 제주특별자치도 (가상)")
st.caption("본 대시보드는 데모 목적으로 제작되었으며, 표시되는 데이터는 실제와 다를 수 있습니다.")
