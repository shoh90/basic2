import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="병해충 분석", layout="wide", page_icon="🐛")

st.title("🐛 병해충 분석")

# ✅ 데이터 로딩
data_dir = "data"
pest_files = ["pest_disease_info_1.csv", "pest_disease_info_2.csv", "pest_disease_info_3.csv"]

dfs = []
for file in pest_files:
    path = os.path.join(data_dir, file)
    if os.path.exists(path):
        df = pd.read_csv(path)
        dfs.append(df)

if not dfs:
    st.error("❗ 병해충 데이터를 불러올 수 없습니다.")
    st.stop()

df_pest = pd.concat(dfs, ignore_index=True)

# ✅ 컬럼명 확인
#st.write("✅ 현재 데이터 컬럼명:", df_pest.columns.tolist())

# ✅ 월 컬럼 생성
if '데이터기준일자' in df_pest.columns:
    df_pest['데이터기준일자'] = pd.to_datetime(df_pest['데이터기준일자'], errors='coerce')
    df_pest['월'] = df_pest['데이터기준일자'].dt.month

# ✅ 필터링 UI
col1, col2 = st.columns(2)

crop_list = df_pest['중점방제대상'].dropna().unique()
crop = col1.selectbox("작물 선택", crop_list)

month_list = sorted(df_pest['월'].dropna().unique())
month = col2.selectbox("월 선택", month_list)

# ✅ 필터링 데이터
filtered = df_pest[(df_pest['중점방제대상'] == crop) & (df_pest['월'] == month)]

# ✅ 병해충 TOP5 (발생건수 기준)
st.subheader(f"📊 {month}월 {crop} 병해충 TOP 5")
if '병해충' in df_pest.columns:
    top5 = filtered['병해충'].value_counts().head(5).reset_index()
    top5.columns = ['병해충명', '발생건수']

    fig = px.bar(top5, x='병해충명', y='발생건수', color='병해충명',
                 labels={'발생건수': '발생 건수'}, title="병해충 TOP 5")
    st.plotly_chart(fig)
else:
    st.warning("'병해충' 컬럼이 없습니다.")

# ✅ 병해충 월별 위험도 추이
st.subheader(f"📈 {crop} 병해충 월별 위험도")
if '위험도지수' in df_pest.columns:
    trend = df_pest[df_pest['중점방제대상'] == crop].groupby('월')['위험도지수'].mean().reset_index()

    fig2 = px.line(trend, x='월', y='위험도지수', markers=True,
                   title="월별 위험도 평균", labels={'위험도지수': '위험도'})
    st.plotly_chart(fig2)
else:
    st.info("❗ '위험도지수' 컬럼이 없습니다.")

# ✅ 방제약 정보 표 (TOP5 병해충 대상)
st.subheader(f"🧪 {crop} 방제약 정보")
if '방제약' in df_pest.columns:
    pest_list = top5['병해충명'].tolist()
    chem_df = filtered[filtered['병해충'].isin(pest_list)][['병해충', '방제약']].drop_duplicates()

    if not chem_df.empty:
        st.dataframe(chem_df, use_container_width=True)
    else:
        st.info(f"{crop}의 방제약 정보가 없습니다.")
else:
    st.warning("❗ '방제약' 컬럼이 존재하지 않습니다.")
