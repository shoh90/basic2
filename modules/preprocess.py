import pandas as pd
import streamlit as st

def preprocess_weather(df, debug=False):
    """기상 데이터 전처리"""
    if debug:
        st.info("📦 기상 데이터 전처리 중...")

    if '일시' in df.columns:
        df['일시'] = pd.to_datetime(df['일시'], errors='coerce')

    target_keywords = ['기온', '강수량', '습도', '풍속']
    for key in target_keywords:
        target_cols = [col for col in df.columns if key in col]
        for col in target_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df

def preprocess_sunshine(df, debug=False):
    """일조량 데이터 전처리"""
    if debug:
        st.info("🌞 일조량 데이터 전처리 중...")

    if '일시' in df.columns:
        df['일시'] = pd.to_datetime(df['일시'], errors='coerce')
    if '일조시간(hr)' in df.columns:
        df['일조시간(hr)'] = pd.to_numeric(df['일조시간(hr)'], errors='coerce').fillna(0)

    return df

def preprocess_pest_disease(df, debug=False):
    """병해충 데이터 전처리"""
    if debug:
        st.info("🐛 병해충 데이터 전처리 중...")

    if '월' in df.columns:
        df['월'] = pd.to_numeric(df['월'], errors='coerce').fillna(0).astype(int)
    if '위험도지수' in df.columns:
        df['위험도지수'] = pd.to_numeric(df['위험도지수'], errors='coerce').fillna(0)

    return df
