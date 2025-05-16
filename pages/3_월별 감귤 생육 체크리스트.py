import streamlit as st
import pandas as pd

st.set_page_config(page_title="감귤 맞춤 조언", layout="wide", page_icon="🍊")

st.title("🍊 감귤 맞춤 월별 조언")

# ✅ 감귤 전용 데이터
citrus_advice = {
    3: {
        "info": "꽃눈이 분화되고 초기 수분관리가 중요한 시기입니다.",
        "warning": "봄 가뭄 대비 물주기 & 진딧물 예찰 필요",
        "image": "https://cdn.pixabay.com/photo/2017/01/20/15/06/oranges-1995056_1280.jpg",
        "todo": ["수분 관리 강화", "진딧물 예찰", "토양 배수 점검"],
        "progress": 20
    },
    5: {
        "info": "꽃이 지고 열매가 맺히는 시기입니다. 물 관리와 병해충 주의가 필요합니다.",
        "warning": "진딧물, 깍지벌레 방제 집중",
        "image": "https://cdn.pixabay.com/photo/2015/12/01/20/28/mandarin-1078065_1280.jpg",
        "todo": ["과일 비대기 물주기", "병해충 방제", "비료 살포"],
        "progress": 40
    },
    10: {
        "info": "수확기를 앞두고 과일 비대와 착색이 진행됩니다.",
        "warning": "탄저병 발생 주의 → 방제 필수",
        "image": "https://cdn.pixabay.com/photo/2017/01/20/15/06/oranges-1995056_1280.jpg",
        "todo": ["착색 촉진 관리", "탄저병 방제", "조기 수확 준비"],
        "progress": 90
    }
}

# ✅ 월 선택
month = st.selectbox("월을 선택하세요", list(range(1, 13)))

# ✅ 데이터 조회
advice = citrus_advice.get(month, None)

if advice:
    col1, col2 = st.columns([2, 1])

    # ✅ 왼쪽: 정보 + 주의사항
    with col1:
        st.success(f"✅ {month}월 감귤 관리 포인트")
        st.markdown(f"### 📌 작업 조언\n- {advice['info']}")
        st.warning(f"⚠️ {advice['warning']}")

        st.subheader("📝 이번 달 할 일 체크리스트")
        for task in advice['todo']:
            st.checkbox(task, value=False)

        st.subheader("🎨 착색 진행률")
        st.progress(advice['progress'] / 100)

    # ✅ 오른쪽: 이미지
    with col2:
        st.image(advice['image'], caption=f"{month}월 감귤 생육 예시", use_container_width=True)

else:
    st.info(f"현재 {month}월 감귤 조언 데이터가 없습니다.")
