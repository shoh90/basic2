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
st.write("✅ 현재 데이터 컬럼명:", df_pest.columns)

# ✅ 월 추출
if '데이터기준일자' in df_pest.columns:
    df_pest['데이터기준일자'] = pd.to_datetime(df_pest['데이터기준일자'], errors='coerce')
    df_pest['월'] = df_pest['데이터기준일자'].dt.month

# ✅ 발생밀도 유사 컬럼 찾기
density_col = '발생밀도'
if '발생밀도' not in df_pest.columns:
    candidates = [col for col in df_pest.columns if '밀도' in col or '위험도' in col]
    if candidates:
        density_col = candidates[0]
    else:
        st.error("❗ '발생밀도' 컬럼을 찾을 수 없습니다.")
        st.stop()

# ✅ 필터 (작물명 & 월)
col1, col2 = st.columns(2)
crop_list = df_pest['중점방제대상'].dropna().unique()
crop = col1.selectbox("작물 선택", crop_list)

month_list = sorted(df_pest['월'].dropna().unique())
month = col2.selectbox("월 선택", month_list)

# ✅ 필터링 데이터
filtered_df = df_pest[(df_pest['중점방제대상'] == crop) & (df_pest['월'] == month)]

if filtered_df.empty:
    st.warning(f"❗ {month}월 {crop} 데이터가 없습니다.")
    st.stop()

# ✅ 병해충 TOP5 차트
top5 = (filtered_df.groupby('병해충')[density_col].mean()
        .sort_values(ascending=False).head(5).reset_index())

st.subheader(f"📊 {month}월 {crop} 병해충 TOP 5")
fig = px.bar(top5, x='병해충', y=density_col, title=f"{month}월 {crop} 병해충 TOP 5")
st.plotly_chart(fig)

# ✅ 상세 원본 데이터 표
st.subheader("📋 상세 병해충 데이터 (표 보기)")
st.dataframe(filtered_df, use_container_width=True)

# ✅ 방제약 정보 표 (TOP5 병해충 대상)
st.subheader(f"🧪 {crop} 병해충 방제약 정보")

if '방제약' in df_pest.columns:
    pest_list = top5['병해충'].tolist()
    chem_df = filtered_df[filtered_df['병해충'].isin(pest_list)][['병해충', '방제약']].drop_duplicates()

    if not chem_df.empty:
        st.dataframe(chem_df, use_container_width=True)
    else:
        st.info(f"❗ {crop}의 방제약 정보가 없습니다.")
else:
    st.warning("❗ '방제약' 컬럼이 존재하지 않습니다.")
