import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from modules.db_loader import load_data

# ─────────────────────────────────────────────
# 기본 설정
st.set_page_config(page_title="감귤 생산성 리포트", layout="wide")
st.title("🍊 감귤 생산성 인사이트 리포트")

# ─────────────────────────────────────────────
# 데이터 로드
df_weather, df_sunshine, df_pest_4, df_pest_5 = load_data()

# ─────────────────────────────────────────────
# coords.xlsx 파일 로딩 (경로 오류 방지)
base_dir = os.path.dirname(os.path.abspath(__file__))
coords_file_path = os.path.join(base_dir, 'data', 'coords.xlsx')

if not os.path.exists(coords_file_path):
    st.error(f"[오류] coords.xlsx 파일이 존재하지 않습니다: {coords_file_path}")
else:
    coords_df = pd.read_excel(coords_file_path, engine='openpyxl')
    st.sidebar.success("✅ coords.xlsx 파일 로드 성공")
    st.sidebar.write(coords_df.head())

# ─────────────────────────────────────────────
# 데이터 로드 결과 디버그
st.subheader("📊 데이터 로드 결과")
st.write("asos_weather", df_weather.shape, df_weather.head())
st.write("sunshine_data", df_sunshine.shape, df_sunshine.head())
st.write("pest_disease_4", df_pest_4.shape, df_pest_4.head())
st.write("pest_disease_5", df_pest_5.shape, df_pest_5.head())

# ─────────────────────────────────────────────
# 감귤 생산현황 - 안전하게 컬럼 매핑
if '재배면적(ha)' in df_pest_4.columns and '재배량(톤)' in df_pest_4.columns:
    df_pest_4 = df_pest_4.rename(columns={'재배면적(ha)': '면적', '재배량(톤)': '생산량'})
    df_pest_4[['면적', '생산량']] = df_pest_4[['면적', '생산량']].apply(pd.to_numeric, errors='coerce').fillna(0)
else:
    st.error("❗ pest_disease_4의 컬럼명이 다릅니다. '재배면적(ha)', '재배량(톤)'이 없습니다.")

if '재배면적(ha)' in df_pest_5.columns and '재배량(톤)' in df_pest_5.columns and '농가수(호)' in df_pest_5.columns:
    df_pest_5 = df_pest_5.rename(columns={'재배면적(ha)': '면적', '재배량(톤)': '생산량', '농가수(호)': '농가수'})
    df_pest_5[['면적', '생산량', '농가수']] = df_pest_5[['면적', '생산량', '농가수']].apply(pd.to_numeric, errors='coerce').fillna(0)
else:
    st.error("❗ pest_disease_5의 컬럼명이 다릅니다. '재배면적(ha)', '재배량(톤)', '농가수(호)'가 없습니다.")

# KPI 및 차트 (데이터가 있을 경우만 진행)
if '면적' in df_pest_4.columns and '면적' in df_pest_5.columns:
    df_seogwipo = df_pest_5.groupby('연도').agg(면적_서귀포=('면적', 'sum'), 생산량_서귀포=('생산량', 'sum'), 농가수_서귀포=('농가수', 'sum')).reset_index()
    df_jeju = df_pest_4.groupby('연도').agg(면적_제주시=('면적', 'sum'), 생산량_제주시=('생산량', 'sum')).reset_index()

    df_total = pd.merge(df_jeju, df_seogwipo, on='연도', how='outer').fillna(0)
    df_total['총재배면적'] = df_total['면적_제주시'] + df_total['면적_서귀포']
    df_total['총생산량(천톤)'] = (df_total['생산량_제주시'] + df_total['생산량_서귀포']) / 1000
    df_total['총농가수'] = df_total['농가수_서귀포']

    latest = df_total.iloc[-1]
    previous = df_total.iloc[-2] if len(df_total) > 1 else latest

    col1, col2, col3 = st.columns(3)
    col1.metric("생산량", f"{latest['총생산량(천톤)']:.0f}천톤", f"{latest['총생산량(천톤)'] - previous['총생산량(천톤)']:.1f}")
    col2.metric("재배면적", f"{latest['총재배면적']:.0f}ha", f"{latest['총재배면적'] - previous['총재배면적']:.1f}")
    col3.metric("농가수", f"{latest['총농가수']:.0f}호", f"{latest['총농가수'] - previous['총농가수']:.1f}")

    st.subheader("📈 감귤 생산 현황 차트")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df_total['연도'], y=df_total['총생산량(천톤)'], name="생산량(천톤)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_total['연도'], y=df_total['총재배면적'], name="재배면적(ha)"), secondary_y=True)
    fig.update_layout(title="연도별 감귤 생산 현황", xaxis_title="연도")
    fig.update_yaxes(title_text="생산량(천톤)", secondary_y=False)
    fig.update_yaxes(title_text="재배면적(ha)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("❗ 감귤 생산 데이터가 부족하여 KPI 및 차트를 표시할 수 없습니다.")

# ─────────────────────────────────────────────
# 기상 데이터 시각화
st.header("🌡️ 기상 데이터 (asos_weather)")
if not df_weather.empty and '지점명' in df_weather.columns and '평균기온(°C)' in df_weather.columns:
    stations = df_weather['지점명'].unique()
    selected_station = st.selectbox("지점 선택 (기온)", stations)
    df_station = df_weather[df_weather['지점명'] == selected_station]
    fig_weather = px.line(df_station, x='일시', y='평균기온(°C)', title=f'{selected_station} 월별 평균기온')
    st.plotly_chart(fig_weather, use_container_width=True)

# ─────────────────────────────────────────────
# 일조시간 데이터 시각화
st.header("🌞 일조시간 데이터 (sunshine_data)")
if not df_sunshine.empty and '지점명' in df_sunshine.columns and '일조시간(hr)' in df_sunshine.columns:
    stations_sun = df_sunshine['지점명'].unique()
    selected_station_sun = st.selectbox("지점 선택 (일조시간)", stations_sun)
    df_station_sun = df_sunshine[df_sunshine['지점명'] == selected_station_sun]
    fig_sunshine = px.line(df_station_sun, x='일시', y='일조시간(hr)', title=f'{selected_station_sun} 월별 일조시간')
    st.plotly_chart(fig_sunshine, use_container_width=True)
