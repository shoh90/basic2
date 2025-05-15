import pandas as pd
import streamlit as st

def preprocess_weather(df):
    """
    기상 데이터 전처리: 날짜형 변환, 결측치 처리, 숫자형 변환 (자동 컬럼 체크 포함)
    """
    st.info("📦 기상 데이터 전처리 중...")

    # 날짜형 변환 (일시 컬럼 있을 때만)
    if '일시' in df.columns:
        df['일시'] = pd.to_datetime(df['일시'], errors='coerce')

    # 숫자형 변환 대상 키워드 목록
    target_keywords = ['기온', '강수량', '습도', '풍속']

    # 해당 키워드가 들어간 컬럼들만 처리
    for key in target_keywords:
        target_cols = [col for col in df.columns if key in col]
        for col in target_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df

def preprocess_sunshine(df):
    """
    일조량 데이터 전처리
    """
    st.info("🌞 일조량 데이터 전처리 중...")

    if '일시' in df.columns:
        df['일시'] = pd.to_datetime(df['일시'], errors='coerce')
    if '일조시간(hr)' in df.columns:
        df['일조시간(hr)'] = pd.to_numeric(df['일조시간(hr)'], errors='coerce').fillna(0)

    return df

def preprocess_pest_disease(df):
    """
    병해충 데이터 전처리: 월, 위험도지수 등
    """
    st.info("🐛 병해충 데이터 전처리 중...")

    if '월' in df.columns:
        df['월'] = pd.to_numeric(df['월'], errors='coerce').fillna(0).astype(int)
    if '위험도지수' in df.columns:
        df['위험도지수'] = pd.to_numeric(df['위험도지수'], errors='coerce').fillna(0)

    return df
