import streamlit as st
import pandas as pd
from modules.load_data import load_data

st.title("🌪️ 이상기후 + 병해충 경고판")

# 데이터 로딩
df_weather, _ = load_data()

# 실제 컬럼명 맞추기 (기준정보에 따라 수정)
print(df_weather.columns)  # 디버그용

# 일강수량 컬럼명 수정 (예: '일강수량' or '일강수량(mm)' 아닌 경우)
rain_col = [col for col in df_weather.columns if '강수' in col][0]
wind_col = [col for col in df_weather.columns if '풍속' in col][0]
humid_col = [col for col in df_weather.columns if '습도' in col][0]

# 연속 무강수 계산
df_weather['연속무강수'] = df_weather[rain_col].rolling(5).apply(lambda x: (x == 0).sum(), raw=True)

# 경고 기준 적용
df_weather['고온경고'] = df_weather['평균기온(°C)'] >= 30
df_weather['강풍경고'] = df_weather[wind_col] >= 10

# 병해충 경고 기준 예시
df_weather['병해충_곰팡이'] = (df_weather['평균기온(°C)'] >= 25) & (df_weather[humid_col] >= 80)
df_weather['병해충_해충'] = (df_weather['평균기온(°C)'] >= 20) & (df_weather['연속무강수'] >= 7)

# 경고 필터링
alerts_df = df_weather[
    (df_weather['연속무강수'] >= 5) |
    (df_weather['고온경고']) |
    (df_weather['강풍경고']) |
    (df_weather['병해충_곰팡이']) |
    (df_weather['병해충_해충'])
]

# 결과 출력
st.dataframe(alerts_df[['일시', '지점명', '평균기온(°C)', wind_col, '연속무강수', '고온경고', '강풍경고', '병해충_곰팡이', '병해충_해충']])
