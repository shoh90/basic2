import streamlit as st
import plotly.express as px
from modules.load_data import load_data

st.title("☀️ 지점별 월별 일조/일사 데이터")

# 데이터 로딩
_, df_sunshine = load_data()

# 지점 선택
selected_sites = st.multiselect('지점을 선택하세요', df_sunshine['지점명'].unique(), default=df_sunshine['지점명'].unique())

# 연월 컬럼 생성
df_sunshine['연월'] = df_sunshine['일시'].dt.to_period('M').astype(str)

# 선택된 지점 필터링
df_selected = df_sunshine[df_sunshine['지점명'].isin(selected_sites)]

# 월별 평균 집계
df_monthly = df_selected.groupby(['연월', '지점명']).agg({
    '일조시간': 'mean',
    '일사량': 'mean'
}).reset_index()

# 시각화
for col, title in [('일조시간', '월별 평균 일조시간'), ('일사량', '월별 평균 일사량')]:
    fig = px.line(df_monthly, x='연월', y=col, color='지점명', markers=True, title=title)
    st.plotly_chart(fig, use_container_width=True)
