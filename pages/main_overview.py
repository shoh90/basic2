import streamlit as st
from modules.db_loader import load_db_table
from modules.preprocess import preprocess_weather
from modules.unified_utils import get_column

st.header("🏠 제주 농부 대시보드 - 전체 요약")

# 데이터 로드 & 전처리
df_weather = load_db_table('asos_weather')
df_weather = preprocess_weather(df_weather)

# 오늘 데이터 추출
today = df_weather['일시'].max()
today_data = df_weather[df_weather['일시'] == today]

# 컬럼명 자동 탐색
temp_col = get_column(df_weather, ['기온'])
rain_col = get_column(df_weather, ['강수량'])
wind_col = get_column(df_weather, ['풍속'])

# 값 표시 (값이 없을 때도 안전하게)
col1, col2, col3 = st.columns(3)

if not today_data.empty:
    col1.metric("🌡 평균기온(°C)", f"{today_data[temp_col].values[0]:.1f}")
    col2.metric("🌧 일강수량(mm)", f"{today_data[rain_col].values[0]:.1f}")
    col3.metric("💨 평균풍속(m/s)", f"{today_data[wind_col].values[0]:.1f}")
else:
    st.warning("❗ 오늘 날짜 데이터가 없습니다.")
