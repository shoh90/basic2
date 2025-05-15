import streamlit as st
import pandas as pd
import plotly.express as px
from modules.db_loader import load_csv
from modules.preprocess import preprocess_pest_disease

st.header("🐛 병해충 분석")

df1 = load_csv('pest_disease_info_1.csv')
df2 = load_csv('pest_disease_info_2.csv')
df3 = load_csv('pest_disease_info_3.csv')
df_pest = pd.concat([df1, df2, df3], ignore_index=True)
df_pest = preprocess_pest_disease(df_pest)

col1, col2, col3 = st.columns(3)
crop = col1.selectbox("작물 선택", df_pest['작물명'].unique())
region = col2.selectbox("지역 선택", df_pest['지역명'].unique())
month = col3.selectbox("월 선택", sorted(df_pest['월'].unique()))

filtered = df_pest[
    (df_pest['작물명'] == crop) &
    (df_pest['지역명'] == region) &
    (df_pest['월'] == month)
]

st.subheader(f"📊 {month}월 {region} {crop} 병해충 TOP 5")
top5 = filtered['병해충명'].value_counts().head(5).reset_index()
top5.columns = ['병해충명', '발생건수']

fig = px.bar(top5, x='병해충명', y='발생건수', color='병해충명',
             labels={'발생건수': '발생 건수'}, title="병해충 TOP 5")
st.plotly_chart(fig)

st.subheader(f"📈 {region} {crop} 병해충 월별 위험도")
trend = df_pest[
    (df_pest['작물명'] == crop) &
    (df_pest['지역명'] == region)
].groupby('월')['위험도지수'].mean().reset_index()

fig2 = px.line(trend, x='월', y='위험도지수', markers=True,
               title="월별 위험도 평균", labels={'위험도지수': '위험도'})
st.plotly_chart(fig2)

if not filtered.empty:
    st.warning(f"⚠️ {month}월 {region} 지역의 {crop}는 '{top5.iloc[0]['병해충명']}' 피해 주의!")
