import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.header("🥕 작물 맞춤 조언")

# 월 선택
month = st.selectbox("월을 선택하세요", list(range(1, 13)))

# 작물 선택
advice_data = {
    "감귤": {
        5: {
            "info": "꽃이 지고 열매가 맺히는 시기입니다. 물 관리와 병해충 주의가 필요합니다.",
            "warning": "진딧물, 깍지벌레 등 병해충 집중 방제 필요!"
        },
        10: {
            "info": "수확기를 앞두고 과일비대가 진행됩니다. 영양관리 및 착색 관리 중요.",
            "warning": "탄저병 발생 가능성 높음 → 방제 필수"
        }
    },
    "배추": {
        5: {
            "info": "초기 생육 촉진을 위한 잡초 제거 및 배수관리 필요.",
            "warning": "뿌리혹병, 해충(배추좀나방) 방제 필요"
        },
        9: {
            "info": "가을배추 정식 시기입니다. 초기 활착 관리 중요.",
            "warning": "고온기 뿌리썩음병 주의"
        }
    }
}

crop = st.selectbox("작물을 선택하세요", list(advice_data.keys()))

# 데이터 조회
crop_advice = advice_data.get(crop, {}).get(month, None)

if crop_advice:
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"✅ {crop} {month}월 조언")
        st.markdown(crop_advice['info'])
    with col2:
        st.warning(f"⚠️ {crop} {month}월 주의사항")
        st.markdown(crop_advice['warning'])
else:
    st.info(f"현재 {crop}의 {month}월 조언 데이터가 없습니다.")
