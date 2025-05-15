import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="병해충 방제약 안내", layout="wide", page_icon="🐛")

st.title("🐛 병해충 방제약 안내")

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
st.write("✅ 현재 데이터 컬럼명:", df_pest.columns.tolist())

# ✅ 필터링 UI
col1, col2 = st.columns(2)

crop_list = df_pest['중점방제대상'].dropna().unique()
crop = col1.selectbox("작물 선택", crop_list)

pest_list = df_pest['병해충'].dropna().unique()
pest = col2.selectbox("병해충 선택", pest_list)

# ✅ 필터링된 방제약 정보
filtered_df = df_pest[(df_pest['중점방제대상'] == crop) & (df_pest['병해충'] == pest)]

st.subheader(f"🧪 {crop} - {pest} 방제약 정보")

if not filtered_df.empty:
    st.dataframe(filtered_df[['병해충', '방제약', '데이터기준일자']], use_container_width=True)
else:
    st.info("❗ 해당 조건의 방제약 정보가 없습니다.")
