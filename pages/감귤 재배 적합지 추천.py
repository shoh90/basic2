import streamlit as st
import pandas as pd
import folium
import sqlite3
from streamlit_folium import st_folium
import numpy as np # pd.NA 대신 사용 가능

# 페이지 설정
st.set_page_config(page_title="감귤 재배 적합지 추천", layout="wide", page_icon="🍊")

st.title("🍊 감귤 재배 적합지 추천")
st.markdown("2020~2024년 데이터를 기준으로 특정 월의 감귤 재배 적합도를 지도에서 확인하세요.")

# 데이터 로딩
@st.cache_data
def load_data():
    try:
        conn = sqlite3.connect('data/asos_weather.db')
        df_weather_raw = pd.read_sql("SELECT * FROM asos_weather", conn)
    except sqlite3.OperationalError as e:
        st.error(f"DB 오류: {e}. 'data/asos_weather.db' 확인 필요.")
        st.stop()
    finally:
        if 'conn' in locals() and conn:
            conn.close()

    try:
        df_citrus_raw = pd.read_excel('data/5.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})
    except FileNotFoundError:
        st.error("'data/5.xlsx' 파일 없음. 확인 필요.")
        st.stop()

    try:
        df_coords_raw = pd.read_excel('data/coords.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})
    except FileNotFoundError:
        st.error("'data/coords.xlsx' 파일 없음. 확인 필요.")
        st.stop()
    return df_weather_raw, df_citrus_raw, df_coords_raw

df_weather, df_citrus, df_coords = load_data()

# --- 전처리 ---
# df_weather
df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['연도'] = df_weather['일시'].dt.year
df_weather['월'] = df_weather['일시'].dt.month
df_weather_filtered = df_weather[df_weather['연도'].between(2020, 2024)].copy() # 20~24년 제한 및 SettingWithCopyWarning 방지

if df_weather_filtered.empty:
    st.error("2020~2024년 사이의 기상 데이터가 없습니다. 데이터베이스를 확인해주세요.")
    st.stop()

# df_citrus
prod_cols = ['노지온주(극조생)', '노지온주(조생)', '노지온주(보통)', '하우스감귤(조기출하)',
             '비가림(월동)감귤', '만감류(시설)', '만감류(노지)']
existing_prod_cols = [col for col in prod_cols if col in df_citrus.columns]
if not existing_prod_cols:
    df_citrus['총재배량(톤)'] = 0
else:
    df_citrus['총재배량(톤)'] = df_citrus[existing_prod_cols].sum(axis=1, numeric_only=True)
df_citrus['읍면동'] = df_citrus['읍면동'].str.strip()
if '연도' not in df_citrus.columns:
    st.error("df_citrus에 '연도' 컬럼이 없습니다.")
    st.stop()

# df_coords
df_coords['읍면동'] = df_coords['읍면동'].str.strip()

# --- 매핑 테이블 (읍면동 -> 지점명) ---
# 최근접 관측소 대신 수동 매핑 사용
mapping = {
    '애월읍': '제주시', '한림읍': '고산', '한경면': '고산', '조천읍': '제주시',
    '구좌읍': '성산', '남원읍': '서귀포시', '성산읍': '성산', '안덕면': '고산',
    '대정읍': '고산', '표선면': '성산'
}
df_coords['지점명'] = df_coords['읍면동'].map(mapping).fillna('제주시') # 매핑 안되면 제주시로

# --- 사용자 입력: 연도 선택 ---
weather_years = set(df_weather_filtered['연도'].dropna().astype(int).unique())
citrus_years = set(df_citrus['연도'].dropna().astype(int).unique())
available_common_years = sorted(list(weather_years.intersection(citrus_years)), reverse=True)

if not available_common_years:
    st.error("2020-2024년 범위에서 감귤 생산량 데이터와 기상 데이터가 공통으로 존재하는 연도가 없습니다.")
    st.stop()

selected_year = st.selectbox("확인할 연도를 선택하세요 (2020~2024)", available_common_years)

# --- 선택된 연도의 감귤 데이터 준비 ---
df_citrus_selected_year = df_citrus[df_citrus['연도'] == selected_year]
df_base = df_coords.merge(df_citrus_selected_year[['읍면동', '총재배량(톤)']], on='읍면동', how='left')
# df_base에는 이미 '지점명'이 매핑되어 있음

# --- 선택된 연도의 월별 기상 데이터 집계 ---
df_weather_for_year_selection = df_weather_filtered[df_weather_filtered['연도'] == selected_year]

if df_weather_for_year_selection.empty:
    st.warning(f"{selected_year}년에는 집계할 기상 데이터가 없습니다.")
    available_months = []
    df_weather_agg_monthly = pd.DataFrame() # 빈 데이터프레임
else:
    df_weather_agg_monthly = df_weather_for_year_selection.groupby(['지점명', '월']).agg(
        평균기온_C=('평균기온(°C)', 'mean'),
        평균상대습도_perc=('평균상대습도(%)', 'mean'),
        월합강수량_mm=('월합강수량(00~24h만)(mm)', 'sum'), # 월별 합계
        평균풍속_ms=('평균풍속(m/s)', 'mean'),
        합계일조시간_hr=('합계 일조시간(hr)', 'sum')     # 월별 합계
    ).reset_index()
    # 컬럼명 변경 (더 명확하게)
    df_weather_agg_monthly = df_weather_agg_monthly.rename(columns={
        '평균기온_C': '평균기온(°C)',
        '평균상대습도_perc': '평균상대습도(%)',
        '월합강수량_mm': '월합강수량(mm)',
        '평균풍속_ms': '평균풍속(m/s)',
        '합계일조시간_hr': '월합일조시간(hr)'
    })
    available_months = sorted(df_weather_agg_monthly['월'].unique())

# --- 사용자 입력: 월 선택 ---
if not available_months:
    st.warning(f"{selected_year}년에는 선택할 수 있는 월별 기상 데이터가 없습니다.")
    # 이후 로직을 위해 빈 df_final 생성
    df_final = df_base.copy()
    weather_cols_for_nan = ['평균기온(°C)', '평균상대습도(%)', '월합강수량(mm)', '평균풍속(m/s)', '월합일조시간(hr)']
    for col in weather_cols_for_nan:
        df_final[col] = np.nan
    selected_month = None # 월 선택 불가
else:
    selected_month = st.selectbox(f"{selected_year}년도에 분석할 월을 선택하세요", available_months)
    df_weather_selected_month = df_weather_agg_monthly[df_weather_agg_monthly['월'] == selected_month]
    df_final = df_base.merge(df_weather_selected_month, on='지점명', how='left')


# --- 적합도 계산 (월 기준) ---
# "적합"이 안 나오는 경우, 이 기준값을 조정하거나 데이터 분포를 확인해보세요.
# 예를 들어, 강수량 50~200mm는 특정 월에는 너무 많거나 적을 수 있습니다.
# 일조시간도 월별로 편차가 큽니다.
df_final['기온적합'] = df_final['평균기온(°C)'].apply(lambda x: 1 if pd.notnull(x) and 16 <= x <= 23 else 0) # 예: 봄/가을 적온
df_final['습도적합'] = df_final['평균상대습도(%)'].apply(lambda x: 1 if pd.notnull(x) and 60 <= x <= 85 else 0) # 조금 넓게
df_final['강수적합'] = df_final['월합강수량(mm)'].apply(lambda x: 1 if pd.notnull(x) and 30 <= x <= 150 else 0) # 월별 강수량 기준 조정
df_final['풍속적합'] = df_final['평균풍속(m/s)'].apply(lambda x: 1 if pd.notnull(x) and x <= 4 else 0) # 약간 완화
df_final['일조적합'] = df_final['월합일조시간(hr)'].apply(lambda x: 1 if pd.notnull(x) and x >= 100 else 0) # 월별 일조시간 기준 조정

df_final['적합도점수'] = df_final[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
df_final['결과'] = df_final['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('부분적합' if x == 3 else '부적합'))

# --- 지도 시각화 ---
if selected_month: # 월이 선택되었을 때만 지도 표시
    st.subheader(f"🗺️ {selected_year}년 {selected_month}월 감귤 재배 적합도 지도")

    if df_final.empty or '위도' not in df_final.columns or '경도' not in df_final.columns:
        st.warning("지도에 표시할 데이터가 없습니다.")
    else:
        m = folium.Map(location=[33.37, 126.53], zoom_start=9)
        for _, row in df_final.iterrows():
            if pd.notnull(row['위도']) and pd.notnull(row['경도']):
                color = 'green' if row['결과'] == '적합' else ('orange' if row['결과'] == '부분적합' else 'red')
                
                popup_text = f"<b>{row['읍면동']} ({row.get('결과', 'N/A')})</b><br>"
                popup_text += f"적합도점수: {int(row.get('적합도점수', 0))}/5<br>"
                if pd.notnull(row.get('평균기온(°C)')):
                    popup_text += f"평균기온: {row.get('평균기온(°C)', 'N/A'):.1f}°C<br>"
                if pd.notnull(row.get('월합강수량(mm)')):
                    popup_text += f"월강수량: {row.get('월합강수량(mm)', 'N/A'):.1f}mm<br>"
                if pd.notnull(row.get('월합일조시간(hr)')):
                     popup_text += f"월일조: {row.get('월합일조시간(hr)', 'N/A'):.1f}hr"
                
                folium.CircleMarker(
                    location=[row['위도'], row['경도']],
                    radius=max(5, min(row.get('총재배량(톤)', 0) / 2000, 12)) if pd.notnull(row.get('총재배량(톤)')) else 6, # 연간 총재배량 기반 크기
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=f"{row['읍면동']}"
                ).add_to(m)
        st_folium(m, width=1000, height=600)
else:
    st.info(f"{selected_year}년에는 분석할 월별 데이터가 없습니다.")


# --- 적합 지역 요약 ---
if selected_month: # 월이 선택되었을 때만 요약 테이블 표시
    st.write(f"📝 {selected_year}년 {selected_month}월 적합/부분적합 지역 요약")
    summary_cols = ['읍면동', '결과', '적합도점수', '평균기온(°C)', '평균상대습도(%)', '월합강수량(mm)', '평균풍속(m/s)', '월합일조시간(hr)']
    existing_summary_cols = [col for col in summary_cols if col in df_final.columns]
    
    df_summary = df_final[df_final['결과'].isin(['적합', '부분적합'])][existing_summary_cols]
    if not df_summary.empty:
        st.dataframe(df_summary.reset_index(drop=True))
    else:
        st.write("해당 월에 적합 또는 부분적합으로 평가된 지역이 없습니다. 적합도 기준을 확인해보세요.")

st.markdown("""
---
**참고 사항:**
- **데이터 기간:** 기상 데이터는 2020년~2024년 자료, 감귤 생산량은 해당 연도의 자료를 사용합니다.
- **총재배량(지도 마커 크기):** 지도 상의 원 크기는 선택된 연도의 연간 총재배량을 나타냅니다. 월별 분석과는 직접적인 관련이 적을 수 있습니다.
""")
