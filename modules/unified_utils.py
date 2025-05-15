import streamlit as st
import pandas as pd
import plotly.express as px

def get_column(df, keywords, required=True):
    """컬럼명에 키워드가 포함된 첫번째 컬럼명을 반환"""
    candidates = [col for col in df.columns if any(k in col for k in keywords)]
    if not candidates:
        if required:
            st.error(f"❗ '{keywords}' 키워드가 포함된 컬럼이 없습니다.")
            st.stop()
        else:
            return None
    return candidates[0]

def add_month_column(df, date_keywords):
    """날짜 컬럼에서 '월' 컬럼을 추출해서 추가"""
    date_col = get_column(df, date_keywords, required=False)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df['월'] = df[date_col].dt.month
    else:
        st.warning("⚠️ 날짜 기반 '월' 컬럼을 만들 수 없습니다.")
    return df

def render_line_chart(df, x_col, y_col, title, y_label):
    """기본 선+점 그래프 그리기"""
    fig = px.line(df, x=x_col, y=y_col, markers=True, title=title, labels={y_col: y_label})
    fig.update_layout(yaxis_range=[0, None], xaxis_title='날짜')
    st.plotly_chart(fig)
