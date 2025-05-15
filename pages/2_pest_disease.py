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

# ✅ 데이터 합치기
df_pest = pd.concat(dfs, ignore_index=True)

# ✅ 전처리 (월 추출 등)
if '데이터기준일자' in df_pest.columns:
    df_pest['데이터기준일자'] = pd.to_datetime(df_pest['데이터기준일자'], errors='coerce')
    df_pest['월'] = df_pest['데이터기준일자'].dt.month

# ✅ 필터 설정
col1, col2 = st.columns(2)
crop_list = df_pest['중점방제대상'].dropna().unique()
crop = col1.selectbox("작물 선택", crop_list)

month_list = sorted(df_pest['월'].dropna().unique())
month = col2.selectbox("월 선택", month_list)

# ✅ 필터링된 데이터
filtered_df = df_pest[(df_pest['중점방제대상'] == crop) & (df_pest['월'] == month)]

# ✅ 병해충 TOP5 시각화
if not filtered_df.empty:
    top5 = (filtered_df.groupby('병해충')['발생밀도'].mean()
            .sort_values(ascending=False).head(5).reset_index())

    st.subheader(f"📊 {month}월 {crop} 병해충 TOP 5")
    fig = px.bar(top5, x='병해충', y='발생밀도', title=f"{month}월 {crop} 병해충 TOP 5")
    st.plotly_chart(fig)

    # ✅ 병해충 원본 데이터 표 추가
    st.subheader("📋 상세 데이터 (표 보기)")
    st.dataframe(filtered_df, use_container_width=True)

else:
    st.warning(f"{month}월 {crop} 데이터가 없습니다.")
