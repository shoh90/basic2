import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# DB 테이블 매핑
@st.cache_data
def get_table_mapping(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    conn.close()

    expected_tables = ['pest_disease_4', 'pest_disease_5', 'asos_weather']
    return {et: next((t for t in tables if et in t), None) for et in expected_tables}

# 데이터 로딩
@st.cache_data
def load_data(db_path):
    mapping = get_table_mapping(db_path)
    conn = sqlite3.connect(db_path)

    df_pest_4 = pd.read_sql(f"SELECT * FROM {mapping['pest_disease_4']}", conn) if mapping['pest_disease_4'] else pd.DataFrame()
    df_pest_5 = pd.read_sql(f"SELECT * FROM {mapping['pest_disease_5']}", conn) if mapping['pest_disease_5'] else pd.DataFrame()
    df_weather = pd.read_sql(f"SELECT * FROM {mapping['asos_weather']}", conn) if mapping['asos_weather'] else pd.DataFrame()

    conn.close()
    return df_pest_4, df_pest_5, df_weather

# Streamlit 시작
st.set_page_config(page_title="감귤 리포트", layout="wide")
st.title("🍊 감귤 생산성 인사이트 리포트")

# DB 경로
db_path = 'asos_weather.db'
df_pest_4, df_pest_5, df_weather = load_data(db_path)

# 1. KPI 카드 및 생산현황
if not df_pest_4.empty and not df_pest_5.empty:
    # 제주시 (pest_disease_4)
    df_pest_4.rename(columns={'행정구역(읍면동)': '읍면동', '재배면적(ha)': '면적', '재배량(톤)': '생산량'}, inplace=True, errors='ignore')
    df_pest_4[['면적', '생산량']] = df_pest_4[['면적', '생산량']].apply(pd.to_numeric, errors='coerce').fillna(0)

    # 서귀포시 (pest_disease_5)
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

    # KPI
    latest = df_total.iloc[-1]
    previous = df_total.iloc[-2] if len(df_total) > 1 else latest

    col1, col2, col3 = st.columns(3)
    col1.metric("생산량", f"{latest['총생산량(천톤)']:.0f}천톤", f"{latest['총생산량(천톤)'] - previous['총생산량(천톤)']:.1f}")
    col2.metric("재배면적", f"{latest['총재배면적']:.0f}ha", f"{latest['총재배면적'] - previous['총재배면적']:.1f}")
    col3.metric("농가수", f"{latest['총농가수']:.0f}호", f"{latest['총농가수'] - previous['총농가수']:.1f}")

    # 생산현황 차트
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df_total['연도'], y=df_total['총생산량(천톤)'], name="생산량(천톤)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_total['연도'], y=df_total['총재배면적'], name="재배면적(ha)"), secondary_y=True)
    fig.update_layout(title="연도별 감귤 생산현황", xaxis_title="연도")
    fig.update_yaxes(title_text="생산량(천톤)", secondary_y=False)
    fig.update_yaxes(title_text="재배면적(ha)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

# 2. 기상 데이터 시각화
if not df_weather.empty:
    st.subheader("기상 데이터 (월별 평균기온)")
    stations = df_weather['지점명'].unique()
    selected_station = st.selectbox("지점 선택", stations)
    df_station = df_weather[df_weather['지점명'] == selected_station]
    df_station['일시'] = pd.to_datetime(df_station['일시'], errors='coerce')
    fig_weather = px.line(df_station, x='일시', y='평균기온(°C)', title=f'{selected_station} 월별 평균기온')
    st.plotly_chart(fig_weather, use_container_width=True)
