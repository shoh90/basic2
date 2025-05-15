import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(page_title="제주 농부 스마트 대시보드", layout="wide", page_icon="🍊")

st.title("🍊 제주 농부 스마트 대시보드")
st.markdown("제주도 농사에 필요한 모든 정보를 한 곳에서 확인하세요.")

# 데이터 로딩
@st.cache_data
def load_data():
    df_weather = pd.read_sql("SELECT * FROM asos_weather", sqlite3.connect('data/asos_weather.db'))
    df_citrus = pd.read_excel('data/5.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})
    df_coords = pd.read_excel('data/coords.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})
    pest_dfs = [pd.read_csv(f'data/pest_disease_info_{i}.csv') for i in range(1, 4)]
    df_pest = pd.concat(pest_dfs, ignore_index=True)
    return df_weather, df_citrus, df_coords, df_pest

df_weather, df_citrus, df_coords, df_pest = load_data()

# 데이터 전처리
df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['월'] = df_weather['일시'].dt.month
df_weather['연도'] = df_weather['일시'].dt.year

# 적합도 계산용 컬럼 추가
df_weather['기온적합'] = df_weather['평균기온(°C)'].apply(lambda x: 1 if 18 <= x <= 25 else 0)
df_weather['습도적합'] = df_weather['평균상대습도(%)'].apply(lambda x: 1 if 60 <= x <= 75 else 0)
df_weather['강수적합'] = df_weather['월합강수량(00~24h만)(mm)'].apply(lambda x: 1 if x <= 50 else 0)
df_weather['풍속적합'] = df_weather['평균풍속(m/s)'].apply(lambda x: 1 if x <= 5 else 0)
df_weather['일조적합'] = df_weather['합계 일조시간(hr)'].apply(lambda x: 1 if x >= 6 else 0)
df_weather['적합도점수'] = df_weather[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
df_weather['결과'] = df_weather['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('보통' if x >= 2 else '부적합'))

# 감귤 총재배량 계산
prod_cols = ['노지온주(극조생)', '노지온주(조생)', '노지온주(보통)', '하우스감귤(조기출하)',
             '비가림(월동)감귤', '만감류(시설)', '만감류(노지)']
df_citrus['총재배량(톤)'] = df_citrus[prod_cols].sum(axis=1, numeric_only=True)

# 추천 시기 TOP 5
summary = df_weather.groupby(['연도', '월', '결과']).size().unstack(fill_value=0).reset_index()
summary = summary.sort_values(by='적합', ascending=False)
recommended = st.selectbox("📊 추천 시기 (적합한 연월)", summary.head(5).apply(lambda x: f"{x['연도']}년 {x['월']}월 (적합 {x['적합']}건)", axis=1))
selected_year, selected_month = map(int, recommended.split('년')[0]), int(recommended.split('년')[1].split('월')[0])

# 필터 검색: 적합/보통/부적합만 보기
filter_options = st.multiselect("결과 필터링", ['적합', '보통', '부적합'], default=['적합', '보통', '부적합'])

# 데이터 병합
df_weather_month = df_weather[(df_weather['연도'] == selected_year) & (df_weather['월'] == selected_month)]
df_weather_agg = df_weather_month.groupby('지점명').agg({
    '평균기온(°C)': 'mean',
    '평균상대습도(%)': 'mean',
    '월합강수량(00~24h만)(mm)': 'sum',
    '평균풍속(m/s)': 'mean',
    '합계 일조시간(hr)': 'sum'
}).reset_index().rename(columns={'지점명': '읍면동'})

df_coords['읍면동'] = df_coords['읍면동'].str.strip()
df_citrus['읍면동'] = df_citrus['읍면동'].str.strip()
df = df_weather_agg.merge(df_citrus[['읍면동', '총재배량(톤)']], on='읍면동', how='left')
df = df.merge(df_coords, on='읍면동', how='left')

# 최종 적합도 계산
df['기온적합'] = df['평균기온(°C)'].apply(lambda x: 1 if 18 <= x <= 25 else 0)
df['습도적합'] = df['평균상대습도(%)'].apply(lambda x: 1 if 60 <= x <= 75 else 0)
df['강수적합'] = df['월합강수량(00~24h만)(mm)'].apply(lambda x: 1 if x <= 50 else 0)
df['풍속적합'] = df['평균풍속(m/s)'].apply(lambda x: 1 if x <= 5 else 0)
df['일조적합'] = df['합계 일조시간(hr)'].apply(lambda x: 1 if x >= 6 else 0)
df['적합도점수'] = df[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
df['결과'] = df['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('보통' if x >= 2 else '부적합'))

# 필터링 반영
df = df[df['결과'].isin(filter_options)]

# 지도 시각화
st.subheader(f"🗺️ {selected_year}년 {selected_month}월 재배 적합도 (필터: {', '.join(filter_options)})")
m = folium.Map(location=[33.4, 126.5], zoom_start=10)
for _, row in df.iterrows():
    if pd.notnull(row['위도']) and pd.notnull(row['경도']):
        color = 'green' if row['결과'] == '적합' else ('orange' if row['결과'] == '보통' else 'red')
        folium.CircleMarker(
            location=[row['위도'], row['경도']],
            radius=8,
            color=color,
            fill=True,
            fill_opacity=0.7,
            tooltip=f"{row['읍면동']} - {row['결과']}"
        ).add_to(m)

st_folium(m, width=1000, height=600)

# 병해충 정보
st.subheader("🐛 주요 병해충 방제약 정보")
if not df_pest.empty:
    st.dataframe(df_pest[['구분', '중점방제대상', '병해충', '방제약', '데이터기준일자']])
else:
    st.warning("병해충 데이터가 없습니다.")
