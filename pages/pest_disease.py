import streamlit as st
import pandas as pd
import plotly.express as px
from modules.db_loader import load_csv

st.header("🐛 병해충 분석 - 제주 농부 맞춤 경고")

# 1. 데이터 불러오기 (3개 파일 합치기)
df1 = load_csv('pest_disease_info_1.csv')
df2 = load_csv('pest_disease_info_2.csv')
df3 = load_csv('pest_disease_info_3.csv')
df_pest = pd.concat([df1, df2, df3], ignore_index=True)

# 2. 필터 (작물, 지역, 월)
col1, col2, col3 = st.columns(3)
crop = col1.selectbox("작물 선택", df_pest['작물명'].unique())
region = col2.selectbox("지역 선택", df_pest['지역명'].unique())
month = col3.selectbox("월 선택", sorted(df_pest['월'].unique()))

# 3. 필터링된 데이터
filtered = df_pest[
    (df_pest['작물명'] == crop) &
    (df_pest['지역명'] == region) &
    (df_pest['월'] == month)
]

# 4. 위험도 Top 5 병해충
st.subheader(f"📊 {month}월 {region} {crop} 병해충 TOP 5")
top5 = filtered['병해충명'].value_counts().head(5).reset_index()
top5.columns = ['병해충명', '발생건수']

fig = px.bar(top5, x='병해충명', y='발생건수', color='병해충명',
             labels={'발생건수': '발생 건수'}, title="병해충 TOP 5")
st.plotly_chart(fig)

# 5. 월별 발생 패턴 (라인 차트)
st.subheader(f"📈 {region} {crop} 병해충 월별 발생 추이")
month_trend = df_pest[
    (df_pest['작물명'] == crop) &
    (df_pest['지역명'] == region)
].groupby('월')['위험도지수'].mean().reset_index()

fig2 = px.line(month_trend, x='월', y='위험도지수',
               markers=True, labels={'위험도지수': '위험도 지수'},
               title="월별 평균 위험도 추이")
st.plotly_chart(fig2)

# 6. 맞춤 경고 메시지
if not filtered.empty:
    top_disease = top5.iloc[0]['병해충명']
    st.warning(f"⚠️ 주의! 이번 달 {region} 지역의 {crop}에는 '{top_disease}' 피해 위험이 높습니다.")
else:
    st.success(f"😊 현재 {region} 지역의 {crop}에는 특별한 병해충 위험이 없습니다.")

# 7. 지역별 병해충 위험도 지도 (선택적)
st.subheader("🗺️ 제주 지역별 병해충 위험도 (예시 Heatmap)")
# 여기는 coords.xlsx 또는 jeju_geo.json과 연계 필요 (추후 구현 가능)
st.info("※ 지도는 좌표 데이터가 준비되면 구현 가능합니다.")

