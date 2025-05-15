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

# ✅ 컬럼명 확인
st.write("✅ 현재 병해충 데이터 컬럼명:", df_pest.columns)

# '월' 컬럼이 없으면 '발표일' 또는 '데이터기준일자'에서 생성
if '월' not in df_pest.columns:
    date_col_candidates = [col for col in df_pest.columns if '일자' in col or '발표일' in col or '날짜' in col]
    if date_col_candidates:
        date_col = date_col_candidates[0]
        st.info(f"🗓 '월' 정보는 '{date_col}'에서 추출합니다.")
        df_pest[date_col] = pd.to_datetime(df_pest[date_col], errors='coerce')
        df_pest['월'] = df_pest[date_col].dt.month
    else:
        st.error("❗ '월' 컬럼도 없고, 기준이 되는 날짜 컬럼도 없습니다. 데이터 확인 필요.")
        st.stop()

# '중점방제대상'을 작물명으로 사용
if '중점방제대상' not in df_pest.columns:
    st.error("❗ '중점방제대상' 컬럼이 없습니다. 데이터 확인 필요.")
    st.stop()
else:
    crop_col = '중점방제대상'

col1, col2 = st.columns(2)
crop = col1.selectbox("작물 선택", df_pest[crop_col].dropna().unique())
month = col2.selectbox("월 선택", sorted(df_pest['월'].dropna().unique()))

filtered = df_pest[
    (df_pest[crop_col] == crop) &
    (df_pest['월'] == month)
]

st.subheader(f"📊 {month}월 {crop} 병해충 TOP 5")
if '병해충' in df_pest.columns:
    top5 = filtered['병해충'].value_counts().head(5).reset_index()
    top5.columns = ['병해충명', '발생건수']

    fig = px.bar(top5, x='병해충명', y='발생건수', color='병해충명',
                 labels={'발생건수': '발생 건수'}, title="병해충 TOP 5")
    st.plotly_chart(fig)

st.subheader(f"📈 {crop} 병해충 월별 위험도")
if '위험도지수' in df_pest.columns:
    trend = df_pest[df_pest[crop_col] == crop].groupby('월')['위험도지수'].mean().reset_index()
    fig2 = px.line(trend, x='월', y='위험도지수', markers=True,
                   title="월별 위험도 평균", labels={'위험도지수': '위험도'})
    st.plotly_chart(fig2)

if not filtered.empty and '병해충' in filtered.columns:
    top_disease = filtered['병해충'].value_counts().idxmax()
    st.warning(f"⚠️ {month}월 {crop}는 '{top_disease}' 피해 위험이 높습니다!")
