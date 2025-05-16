import streamlit as st
import pandas as pd
import folium
import sqlite3
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(page_title="감귤 재배 적합지 추천", layout="wide", page_icon="🍊")

st.title("🍊 감귤 재배 적합지 추천")
st.markdown("제주도 주요 지역의 감귤 재배량과 재배 적합도를 지도에서 확인하세요.")

# 데이터 로딩 함수
@st.cache_data
def load_data():
    conn = sqlite3.connect('data/asos_weather.db')
    df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
    conn.close()

    df_citrus = pd.read_excel('data/5.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})
    df_coords = pd.read_excel('data/coords.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})

    return df_weather, df_citrus, df_coords

df_weather, df_citrus, df_coords = load_data()

# 전처리
df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['월'] = df_weather['일시'].dt.month
df_weather['연도'] = df_weather['일시'].dt.year

# 총재배량 계산
prod_cols = ['노지온주(극조생)', '노지온주(조생)', '노지온주(보통)', '하우스감귤(조기출하)', '비가림(월동)감귤', '만감류(시설)', '만감류(노지)']
df_citrus['총재배량(톤)'] = df_citrus[prod_cols].sum(axis=1, numeric_only=True)

# 지역 매핑 (정확한 관측소 좌표 기반 매핑 적용 권장)
mapping = {
    '애월읍': '제주시', '한림읍': '고산', '한경면': '고산', '조천읍': '제주시',
    '구좌읍': '성산', '남원읍': '서귀포시', '성산읍': '성산', '안덕면': '고산',
    '대정읍': '고산', '표선면': '성산'
}
df_coords['읍면동'] = df_coords['읍면동'].str.strip()
df_citrus['읍면동'] = df_citrus['읍면동'].str.strip()

# 연도 선택
available_years = sorted(df_citrus['연도'].dropna().astype(int).unique(), reverse=True)
selected_year = st.selectbox("확인할 연도를 선택하세요", available_years)

# 읍면동 기준 병합
df_citrus_selected = df_citrus[df_citrus['연도'] == selected_year]
df_base = df_coords.merge(df_citrus_selected[['읍면동', '총재배량(톤)']], on='읍면동', how='left')
df_base['지점명'] = df_base['읍면동'].map(mapping).fillna('제주시')

# 연도별 기상 집계 (연간 기준)
df_weather_year = df_weather[df_weather['연도'] == selected_year]
df_weather_agg = df_weather_year.groupby('지점명').agg({
    '평균기온(°C)': 'mean',
    '평균상대습도(%)': 'mean',
    '월합강수량(00~24h만)(mm)': 'sum',
    '평균풍속(m/s)': 'mean',
    '합계 일조시간(hr)': 'sum'
}).reset_index()

# 병합
df = df_base.merge(df_weather_agg, on='지점명', how='left')

# 적합도 계산 (연간 기준)
df['기온적합'] = df['평균기온(°C)'].apply(lambda x: 1 if pd.notnull(x) and 15 <= x <= 20 else 0)
df['습도적합'] = df['평균상대습도(%)'].apply(lambda x: 1 if pd.notnull(x) and 60 <= x <= 80 else 0)
df['강수적합'] = df['월합강수량(00~24h만)(mm)'].apply(lambda x: 1 if pd.notnull(x) and 800 <= x <= 1500 else 0)
df['풍속적합'] = df['평균풍속(m/s)'].apply(lambda x: 1 if pd.notnull(x) and x <= 3 else 0)
df['일조적합'] = df['합계 일조시간(hr)'].apply(lambda x: 1 if pd.notnull(x) and x >= 1800 else 0)

df['적합도점수'] = df[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
df['결과'] = df['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('부분적합' if x == 3 else '부적합'))

# 지도 시각화
st.subheader(f"🗺️ {selected_year}년 기준 감귤 재배량 및 적합도 지도")

if not df.empty:
    m = folium.Map(location=[33.37, 126.53], zoom_start=9)
    for _, row in df.iterrows():
        if pd.notnull(row['위도']) and pd.notnull(row['경도']):
            color = 'green' if row['결과'] == '적합' else ('orange' if row['결과'] == '부분적합' else 'red')
            popup = f"""
            <b>{row['읍면동']} ({row['결과']})</b><br>
            총재배량: {row.get('총재배량(톤)', '정보 없음')}톤<br>
            평균기온: {row.get('평균기온(°C)', 'N/A')}°C<br>
            적합도점수: {row['적합도점수']}/5
            """
            folium.CircleMarker(
                location=[row['위도'], row['경도']],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=popup,
                tooltip=row['읍면동']
            ).add_to(m)
    st_folium(m, width=1000, height=600)
else:
    st.warning("지도에 표시할 데이터가 없습니다.")

# 적합/부분적합 요약
st.write("📝 적합/부분적합 지역 요약")
df_summary = df[df['결과'].isin(['적합', '부분적합'])][['읍면동', '결과', '적합도점수', '총재배량(톤)', '평균기온(°C)', '평균상대습도(%)', '월합강수량(00~24h만)(mm)', '평균풍속(m/s)', '합계 일조시간(hr)']]
if not df_summary.empty:
    st.dataframe(df_summary.reset_index(drop=True))
else:
    st.write("적합 또는 부분적합 지역이 없습니다.")

st.markdown("""
---
📌 주의:  
- 강수량, 일조시간은 **연간 기준**이며, 실측 월별 데이터 사용 시 더욱 정확한 결과 가능  
- 관측소 매핑은 **고산, 성산, 서귀포시, 제주시** 기준 단순화  
- 향후 geopy 거리 기반 자동 매핑 적용 가능
""")
