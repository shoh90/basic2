import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="실시간 기후 모니터링 및 이상기후 알림", layout="wide", page_icon="🌡️")

st.title("🌡️ 실시간 기후 모니터링 및 이상기후 알림")

st.markdown("""
제주도 주요 지역의 **기온, 강수량, 풍속, 주간 예보**를 실시간으로 모니터링합니다.  
이상기후 발생 가능성이 감지될 경우 **⚠️ 경고 알림**을 제공합니다.
""")

# 데이터 로딩 (DB에서 직접)
conn = sqlite3.connect('data/asos_weather.db')
df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
conn.close()

df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['월'] = df_weather['일시'].dt.month
df_weather['연도'] = df_weather['일시'].dt.year

# 오늘 데이터
today = df_weather['일시'].max()
today_data = df_weather[df_weather['일시'] == today]

# ✅ 일기온 (평균기온 → 일기온 문구만 변경)
st.subheader("🌡️ 일기온")
if not today_data.empty:
    fig_temp = px.bar(today_data, x='지점명', y='평균기온(°C)', title=f"{today.date()} 일기온 (°C)")
    st.plotly_chart(fig_temp, use_container_width=True)
else:
    st.warning("오늘 기온 데이터가 없습니다.")

# ✅ 일강수량 → 월합강수량(00~24h만)(mm)로 변경
st.subheader("🌧️ 일강수량")
if not today_data.empty:
    if '월합강수량(00~24h만)(mm)' in today_data.columns:
        fig_rain = px.bar(today_data, x='지점명', y='월합강수량(00~24h만)(mm)', title=f"{today.date()} 일강수량 (mm)")
        st.plotly_chart(fig_rain, use_container_width=True)
    else:
        st.warning("📛 '월합강수량(00~24h만)(mm)' 컬럼이 없습니다.")
else:
    st.warning("오늘 강수 데이터가 없습니다.")

# ✅ 평균풍속
st.subheader("💨 평균풍속")
if not today_data.empty:
    fig_wind = px.bar(today_data, x='지점명', y='평균풍속(m/s)', title=f"{today.date()} 평균풍속 (m/s)")
    st.plotly_chart(fig_wind, use_container_width=True)
else:
    st.warning("오늘 풍속 데이터가 없습니다.")

# ✅ 주간 강수 예보 (가상 예시)
st.subheader("📅 주간 강수량 예보")
dummy = pd.DataFrame({
    '날짜': pd.date_range(start=today, periods=7),
    '예상강수량(mm)': [0, 10, 20, 5, 0, 15, 0]
})
fig_forecast = px.bar(dummy, x='날짜', y='예상강수량(mm)', title="주간 강수 예보 (mm)")
st.plotly_chart(fig_forecast, use_container_width=True)

# ✅ 이상기후 경고 (가상 로직 예시)
# 안전하게 컬럼 확인 → 없으면 오류 없이 넘어감
def get_col_mean(df, col):
    if col in df.columns:
        return df[col].mean()
    else:
        st.warning(f"❗ 컬럼 '{col}'이 없습니다.")
        return None

st.subheader("⚠️ 이상기후 경고")
warnings = []

if get_col_mean(today_data, '평균기온(°C)') and get_col_mean(today_data, '평균기온(°C)') >= 30:
    warnings.append("🔥 고온주의보 (평균기온 30도 이상)")

if get_col_mean(today_data, '월합강수량(00~24h만)(mm)') and get_col_mean(today_data, '월합강수량(00~24h만)(mm)') <= 1:
    warnings.append("💧 무강수 경고 (1mm 이하)")

if get_col_mean(today_data, '평균풍속(m/s)') and get_col_mean(today_data, '평균풍속(m/s)') >= 8:
    warnings.append("🌪️ 강풍주의보 (풍속 8m/s 이상)")

if warnings:
    for w in warnings:
        st.error(w)
else:
    st.success("현재 이상기후 경고 없음.")
