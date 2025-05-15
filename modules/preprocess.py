import pandas as pd
import streamlit as st

def preprocess_weather(df):
    """
    기상 데이터 전처리: 날짜형 변환, 결측치 처리, 숫자형 변환
    """
    st.info("📦 기상 데이터 전처리 중...")

    # 날짜형 변환
    df['일시'] = pd.to_datetime(df['일시'], errors='coerce')

    # 숫자형 변환 및 결측치 처리
    num_cols = ['평균기온(°C)', '일강수량(mm)', '평균 상대습도(%)', '평균 풍속(m/s)']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df

def preprocess_sunshine(df):
    """
    일조량 데이터 전처리
    """
    st.info("🌞 일조량 데이터 전처리 중...")

    df['일시'] = pd.to_datetime(df['일시'], errors='coerce')
    df['일조시간(hr)'] = pd.to_numeric(df['일조시간(hr)'], errors='coerce').fillna(0)

    return df

def preprocess_pest_disease(df):
    """
    병해충 데이터 전처리: 월, 위험도지수 변환 등
    """
    st.info("🐛 병해충 데이터 전처리 중...")

    df['월'] = pd.to_numeric(df['월'], errors='coerce').fillna(0).astype(int)
    df['위험도지수'] = pd.to_numeric(df['위험도지수'], errors='coerce').fillna(0)

    return df
