import streamlit as st
import pandas as pd
import folium
import sqlite3
from streamlit_folium import st_folium
import numpy as np

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
if df_weather.empty:
    st.error("기상 데이터를 불러오지 못했습니다.")
    st.stop()

df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['연도'] = df_weather['일시'].dt.year
df_weather['월'] = df_weather['일시'].dt.month
df_weather_filtered = df_weather[df_weather['연도'].between(2020, 2024)].copy()

if df_weather_filtered.empty:
    st.error("2020~2024년 사이의 기상 데이터가 없습니다. 데이터베이스를 확인해주세요.")
    st.stop()

# df_citrus
if df_citrus.empty:
    st.error("감귤 생산량 데이터를 불러오지 못했습니다.")
    st.stop()
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
if df_coords.empty:
    st.error("좌표 데이터를 불러오지 못했습니다.")
    st.stop()
df_coords['읍면동'] = df_coords['읍면동'].str.strip()

# --- 매핑 테이블 (읍면동 -> 지점명) ---
# 실제 DB의 지점명과 일치시켜야 함. (예: '제주', '서귀포', '고산', '성산')
# CSV 파일에 지점명이 '제주', '서귀포' 등으로 되어있으므로 이를 반영.
# 만약 DB에 '제주시', '서귀포시'로 되어있다면 mapping 값도 그렇게 수정해야 함.
mapping = {
    '애월읍': '제주', '한림읍': '고산', '한경면': '고산', '조천읍': '제주',
    '구좌읍': '성산', '남원읍': '서귀포', '성산읍': '성산', '안덕면': '고산',
    '대정읍': '고산', '표선면': '성산'
}
df_coords['지점명'] = df_coords['읍면동'].map(mapping).fillna('제주') # 매핑 안되면 '제주'로 (DB에 '제주' 지점명 필요)

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

# --- 선택된 연도의 월별 기상 데이터 집계 ---
df_weather_for_year_selection = df_weather_filtered[df_weather_filtered['연도'] == selected_year]

# 원본 데이터의 기상 컬럼명 (DB/CSV 컬럼명과 일치)
weather_original_cols = ['평균기온(°C)', '평균상대습도(%)', '월합강수량(00~24h만)(mm)', '평균풍속(m/s)', '합계 일조시간(hr)']
# 집계 후 사용할 분석용 컬럼명
weather_analysis_cols = ['평균기온(°C)', '평균상대습도(%)', '월합강수량(mm)', '평균풍속(m/s)', '월합일조시간(hr)']

if df_weather_for_year_selection.empty:
    st.warning(f"{selected_year}년에는 집계할 기상 데이터가 없습니다.")
    available_months = []
    df_weather_agg_monthly = pd.DataFrame(columns=['지점명', '월'] + weather_analysis_cols)
else:
    # agg_dict 수정:
    # key: 최종적으로 생성될 컬럼명 (weather_analysis_cols 사용)
    # value: NamedAgg 객체, 여기서 column은 원본 DataFrame의 컬럼명 (weather_original_cols 사용)
    agg_dict = {
        weather_analysis_cols[0]: pd.NamedAgg(column=weather_original_cols[0], aggfunc='mean'),
        weather_analysis_cols[1]: pd.NamedAgg(column=weather_original_cols[1], aggfunc='mean'),
        weather_analysis_cols[2]: pd.NamedAgg(column=weather_original_cols[2], aggfunc='sum'),
        weather_analysis_cols[3]: pd.NamedAgg(column=weather_original_cols[3], aggfunc='mean'),
        weather_analysis_cols[4]: pd.NamedAgg(column=weather_original_cols[4], aggfunc='sum'),
    }
    # groupby 시 as_index=False를 사용하면 reset_index()를 호출할 필요가 없음
    df_weather_agg_monthly = df_weather_for_year_selection.groupby(['지점명', '월'], as_index=False).agg(**agg_dict)
    available_months = sorted(df_weather_agg_monthly['월'].unique())

# --- 사용자 입력: 월 선택 ---
if not available_months:
    st.warning(f"{selected_year}년에는 선택할 수 있는 월별 기상 데이터가 없습니다.")
    df_final = df_base.copy()
    for col in weather_analysis_cols:
        df_final[col] = np.nan
    selected_month = None
else:
    selected_month = st.selectbox(f"{selected_year}년도에 분석할 월을 선택하세요", available_months)
    df_weather_selected_month = df_weather_agg_monthly[df_weather_agg_monthly['월'] == selected_month]
    df_final = df_base.merge(df_weather_selected_month, on='지점명', how='left')
    for col in weather_analysis_cols:
        if col not in df_final.columns:
            df_final[col] = np.nan


# --- 적합도 계산 (월 기준) ---
default_criteria = {
    '기온': (16, 23), '습도': (60, 85), '강수': (30, 150), '풍속_max': 4, '일조_min': 100
}
special_criteria_nov = {
    '기온': (10, 18), '습도': (55, 80), '강수': (10, 120), '풍속_max': 5, '일조_min': 70
}
special_criteria_winter = {
    '기온': (5, 15), '습도': (50, 80), '강수': (10, 100), '풍속_max': 6, '일조_min': 60
}
special_criteria_summer = {
    '기온': (22, 30), '습도': (70, 90), '강수': (100, 300), '풍속_max': 5, '일조_min': 150
}

criteria_info_text = "일반(봄/가을철) 적합도 기준이 적용되었습니다." # 기본값
if selected_month is not None:
    if selected_month == 11:
        criteria_info_text = "11월 특별 적합도 기준이 적용되었습니다."
        criteria = special_criteria_nov
    elif selected_month in [12, 1, 2]:
        criteria_info_text = "겨울철 특별 적합도 기준이 적용되었습니다."
        criteria = special_criteria_winter
    elif selected_month in [7, 8]:
        criteria_info_text = "여름철 특별 적합도 기준이 적용되었습니다."
        criteria = special_criteria_summer
    else:
        criteria = default_criteria
    st.info(criteria_info_text)

    df_final['기온적합'] = df_final[weather_analysis_cols[0]].apply(lambda x: 1 if pd.notnull(x) and criteria['기온'][0] <= x <= criteria['기온'][1] else 0)
    df_final['습도적합'] = df_final[weather_analysis_cols[1]].apply(lambda x: 1 if pd.notnull(x) and criteria['습도'][0] <= x <= criteria['습도'][1] else 0)
    df_final['강수적합'] = df_final[weather_analysis_cols[2]].apply(lambda x: 1 if pd.notnull(x) and criteria['강수'][0] <= x <= criteria['강수'][1] else 0)
    df_final['풍속적합'] = df_final[weather_analysis_cols[3]].apply(lambda x: 1 if pd.notnull(x) and x <= criteria['풍속_max'] else 0)
    df_final['일조적합'] = df_final[weather_analysis_cols[4]].apply(lambda x: 1 if pd.notnull(x) and x >= criteria['일조_min'] else 0)

    df_final['적합도점수'] = df_final[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
    df_final['결과'] = df_final['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('부분적합' if x >= 2 else '부적합'))
else:
    df_final['기온적합'] = 0
    df_final['습도적합'] = 0
    df_final['강수적합'] = 0
    df_final['풍속적합'] = 0
    df_final['일조적합'] = 0
    df_final['적합도점수'] = 0
    df_final['결과'] = '정보 없음'


# --- 지도 시각화 ---
if selected_month:
    st.subheader(f"🗺️ {selected_year}년 {selected_month}월 감귤 재배 적합도 지도")

    if df_final.empty or '위도' not in df_final.columns or '경도' not in df_final.columns:
        st.warning("지도에 표시할 데이터가 없습니다.")
    else:
        m = folium.Map(location=[33.37, 126.53], zoom_start=9)
        for _, row in df_final.iterrows():
            if pd.notnull(row['위도']) and pd.notnull(row['경도']):
                color = 'green' if row['결과'] == '적합' else ('orange' if row['결과'] == '부분적합' else ('red' if row['결과'] == '부적합' else 'grey'))
                
                popup_text = f"<b>{row['읍면동']} ({row.get('결과', 'N/A')})</b><br>"
                popup_text += f"적합도점수: {int(row.get('적합도점수', 0))}/5<br>"
                popup_text += f"가까운 관측소: {row.get('지점명', 'N/A')}<br>"
                if pd.notnull(row.get(weather_analysis_cols[0])):
                    popup_text += f"평균기온: {row.get(weather_analysis_cols[0], 'N/A'):.1f}°C (적합: {row.get('기온적합',0)})<br>"
                if pd.notnull(row.get(weather_analysis_cols[2])):
                    popup_text += f"월강수량: {row.get(weather_analysis_cols[2], 'N/A'):.1f}mm (적합: {row.get('강수적합',0)})<br>"
                if pd.notnull(row.get(weather_analysis_cols[4])):
                     popup_text += f"월일조: {row.get(weather_analysis_cols[4], 'N/A'):.1f}hr (적합: {row.get('일조적합',0)})"
                
                folium.CircleMarker(
                    location=[row['위도'], row['경도']],
                    radius=max(5, min(row.get('총재배량(톤)', 0) / 2000, 12)) if pd.notnull(row.get('총재배량(톤)')) else 6,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    popup=folium.Popup(popup_text, max_width=350),
                    tooltip=f"{row['읍면동']}"
                ).add_to(m)
        st_folium(m, width=1000, height=600)
else:
    st.info(f"{selected_year}년에는 분석할 월별 데이터가 없습니다. 지도와 요약 정보가 제공되지 않습니다.")

# --- 적합 지역 요약 ---
if selected_month:
    st.write(f"📝 {selected_year}년 {selected_month}월 적합/부분적합 지역 요약")
    summary_cols = ['읍면동', '결과', '적합도점수'] + weather_analysis_cols + ['지점명']
    existing_summary_cols = [col for col in summary_cols if col in df_final.columns]
    
    df_summary = df_final[df_final['결과'].isin(['적합', '부분적합'])][existing_summary_cols]
    if not df_summary.empty:
        st.dataframe(df_summary.sort_values(by='적합도점수', ascending=False).reset_index(drop=True))
    else:
        st.write("해당 월에 적합 또는 부분적합으로 평가된 지역이 없습니다. 적합도 기준을 확인하거나 다른 월/연도를 선택해보세요.")

st.markdown("""
---
**참고 사항:**
- **데이터 기간: 기상 데이터는 2020년~2024년 자료, 감귤 생산량은 해당 연도의 자료를 사용합니다.
- **총재배량(지도 마커 크기): 지도 상의 원 크기는 선택된 연도의 연간 총재배량을 나타냅니다.
""")
