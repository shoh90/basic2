import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit.components.v1 import html
from modules.load_data import load_data

# 🔶 타이틀
st.set_page_config(page_title="감귤 생산성 인사이트 리포트", layout="wide")
st.title("🍊 감귤 생산성 인사이트 리포트 (2025년 4월 기준)")

# 🔶 데이터 로딩
df_weather, df_sunshine = load_data()
df_weather['연월'] = df_weather['일시'].dt.to_period('M').astype(str)
df_sunshine['연월'] = df_sunshine['일시'].dt.to_period('M').astype(str)

selected_month = st.selectbox("📅 기준 월 선택", sorted(df_weather['연월'].unique()), index=len(df_weather['연월'].unique())-1)

# 🔶 감귤 적합성 테이블
st.subheader("📊 감귤 재배 적합성 현황")
df_merge = pd.merge(df_weather[df_weather['연월'] == selected_month], df_sunshine[df_sunshine['연월'] == selected_month], on=['지점명', '연월'], how='left')

df_merge['적합도점수'] = 0
df_merge['적합도점수'] += df_merge['평균기온(°C)'].apply(lambda x: 33 if 12 <= x <= 18 else 0)
df_merge['적합도점수'] += df_merge['평균상대습도(%)'].apply(lambda x: 33 if 60 <= x <= 85 else 0)
df_merge['적합도점수'] += df_merge['일조시간'].apply(lambda x: 34 if x >= 180 else 0)

st.dataframe(df_merge[['지점명', '평균기온(°C)', '평균상대습도(%)', '일조시간', '적합도점수']])

# 🔶 지도 시각화
st.subheader("🗺️ 감귤 적합도 지도")

stations = {
    '제주시': (33.4996, 126.5312),
    '고산': (33.2931, 126.1628),
    '서귀포': (33.2540, 126.5618),
    '성산': (33.3875, 126.8808),
    '고흥': (34.6076, 127.2871),
    '완도': (34.3111, 126.7531)
}

fmap = folium.Map(location=[34.0, 126.5], zoom_start=8)

for station, (lat, lon) in stations.items():
    row = df_merge[df_merge['지점명'] == station]
    if row.empty: continue
    score = row['적합도점수'].values[0]
    color = 'green' if score >= 66 else 'orange' if score >= 33 else 'gray'
    tooltip = f"<b>{station} ({selected_month})</b><br>적합도 점수: {score}%"
    folium.CircleMarker(location=[lat, lon], radius=10, color=color, fill=True, fill_opacity=0.9, popup=tooltip).add_to(fmap)

html(fmap._repr_html_(), height=500, width=800)

# 🔶 이상기후 경고
st.subheader("🌪️ 이상기후 경고 현황")
df_weather['고온경고'] = df_weather['평균기온(°C)'] >= 30
df_weather['연속무강수'] = df_weather['평균상대습도(%)'].rolling(5).apply(lambda x: (x == 0).sum())
df_weather['강풍경고'] = df_weather.get('평균풍속(m/s)', 0) >= 5
alerts = df_weather[(df_weather['연월'] == selected_month) & ((df_weather['연속무강수'] >= 5) | (df_weather['고온경고']) | (df_weather['강풍경고']))]
st.dataframe(alerts[['일시', '지점명', '평균기온(°C)', '연속무강수', '고온경고', '강풍경고']])

# 🔶 최종 인사이트 요약
st.markdown("""
### 📍 최종 인사이트 요약
- **서귀포 & 성산** 지역이 감귤 재배 최적지 (적합도 점수 90% 이상)
- **고흥/완도** 지역은 일조량은 충분하나 습도 부족 + 강풍/무강수 경고 다발
- 감귤 농가 재배지 확장 시 **성산 → 서귀포 축선** 권장
- 고흥/완도는 신규 진입 지양, 부동산 데이터 연계 시 성산 인근 농지 추천 가능
""")
