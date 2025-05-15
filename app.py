import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import os

# 데이터 로드 모듈 (modules 폴더에 load_data.py, db_loader.py, preprocessing.py 있다고 가정)
from modules.db_loader import load_db_data

# ───────────────────────────────────────────────────────────
# 1. Streamlit 기본 설정
st.set_page_config(page_title="감귤 생산성 리포트", layout="wide")
st.title("🍊 감귤 생산성 인사이트 리포트 (2025 기준)")

# ───────────────────────────────────────────────────────────
# 2. 데이터 로드
db_path = os.path.join("data", "asos_weather.db")
df_pest_4, df_pest_5, df_weather = load_db_data(db_path)

# ───────────────────────────────────────────────────────────
# 3. 디버그 확인 (데이터 유무 체크)
st.subheader("📊 데이터 로드 결과")
st.write("pest_disease_4", df_pest_4.shape, df_pest_4.head())
st.write("pest_disease_5", df_pest_5.shape, df_pest_5.head())
st.write("asos_weather", df_weather.shape, df_weather.head())

# ───────────────────────────────────────────────────────────
# 4. 감귤 생산 KPI 카드
if not df_pest_4.empty and not df_pest_5.empty:
    # pest_disease_4 (제주시)
    df_pest_4 = df_pest_4.rename(columns={'행정구역(읍면동)': '읍면동', '재배면적(ha)': '면적', '재배량(톤)': '생산량'}, errors='ignore')
    df_pest_4[['면적', '생산량']] = df_pest_4[['면적', '생산량']].apply(pd.to_numeric, errors='coerce').fillna(0)

    # pest_disease_5 (서귀포시)
    df_pest_5.columns = df_pest_5.columns.str.strip()
    value_vars = [col for col in df_pest_5.columns if col not in ['연도', '읍면동', '구분', '데이터기준일']]
    df_pest_5_melt = df_pest_5.melt(id_vars=['연도', '읍면동', '구분'], value_vars=value_vars, var_name='품종', value_name='값')
    df_pest_5_pivot = df_pest_5_melt.pivot_table(index=['연도', '읍면동', '품종'], columns='구분', values='값', aggfunc='sum').reset_index()

    # 집계
    df_seogwipo = df_pest_5_pivot.groupby('연도').agg(면적=('면적', 'sum'), 생산량=('생산량', 'sum'), 농가수=('농가수', 'sum')).reset_index()
    df_jeju = df_pest_4.groupby('연도').agg(면적=('면적', 'sum'), 생산량=('생산량', 'sum')).reset_index()

    df_total = pd.merge(df_jeju, df_seogwipo, on='연도', how='outer', suffixes=('_제주시', '_서귀포')).fillna(0)
    df_total['총재배면적'] = df_total['면적_제주시'] + df_total['면적_서귀포']
    df_total['총생산량(천톤)'] = (df_total['생산량_제주시'] + df_total['생산량_서귀포']) / 1000
    df_total['총농가수'] = df_total['농가수']

    # KPI 카드
    st.subheader("✅ KPI 카드")
    latest = df_total.iloc[-1]
    previous = df_total.iloc[-2] if len(df_total) > 1 else latest

    col1, col2, col3 = st.columns(3)
    col1.metric("생산량", f"{latest['총생산량(천톤)']:.0f}천톤", f"{latest['총생산량(천톤)'] - previous['총생산량(천톤)']:.1f}")
    col2.metric("재배면적", f"{latest['총재배면적']:.0f}ha", f"{latest['총재배면적'] - previous['총재배면적']:.1f}")
    col3.metric("농가수", f"{latest['총농가수']:.0f}호", f"{latest['총농가수'] - previous['총농가수']:.1f}")

    # 생산 현황 혼합차트
    st.subheader("📈 연도별 감귤 생산 현황")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df_total['연도'], y=df_total['총생산량(천톤)'], name="생산량(천톤)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_total['연도'], y=df_total['총재배면적'], name="재배면적(ha)"), secondary_y=True)
    fig.update_layout(title="연도별 감귤 생산 현황", xaxis_title="연도")
    fig.update_yaxes(title_text="생산량(천톤)", secondary_y=False)
    fig.update_yaxes(title_text="재배면적(ha)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

# ───────────────────────────────────────────────────────────
# 5. 기상 데이터 시각화
if not df_weather.empty and '지점명' in df_weather.columns and '평균기온(°C)' in df_weather.columns:
    st.subheader("🌡️ 기상 데이터 (월별 평균기온)")
    stations = df_weather['지점명'].unique()
    selected_station = st.selectbox("지점 선택", stations)
    df_station = df_weather[df_weather['지점명'] == selected_station]
    df_station['일시'] = pd.to_datetime(df_station['일시'], errors='coerce')
    fig_weather = px.line(df_station, x='일시', y='평균기온(°C)', title=f'{selected_station} 월별 평균기온')
    st.plotly_chart(fig_weather, use_container_width=True)
else:
    st.warning("asos_weather 데이터에 지점명 또는 평균기온 컬럼이 없습니다.")
