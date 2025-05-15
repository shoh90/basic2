import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
import os
import re # 추천 시기 파싱을 위해 추가

# 페이지 설정
st.set_page_config(page_title="제주 농부 스마트 대시보드", layout="wide", page_icon="🍊")

st.title("🍊 제주 농부 스마트 대시보드")
st.markdown("제주도 농사에 필요한 모든 정보를 한 곳에서 확인하세요.")

# --- 데이터 로딩 함수 (캐싱 적용) ---
@st.cache_data
def load_data():
    # DB 파일 및 Excel 파일 경로 (실제 환경에 맞게 수정)
    db_path = 'data/asos_weather.db'
    citrus_path = 'data/5.xlsx'
    coords_path = 'data/coords.xlsx'
    pest_info_paths = [f'data/pest_disease_info_{i}.csv' for i in range(1, 4)]

    df_weather = pd.DataFrame()
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        try:
            df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
        except Exception as e:
            st.error(f"기상 데이터 로드 오류: {e}")
        conn.close()
    else:
        st.error(f"DB 파일을 찾을 수 없습니다: {db_path}")

    try:
        df_citrus = pd.read_excel(citrus_path)
    except FileNotFoundError:
        st.error(f"파일을 찾을 수 없습니다: {citrus_path}")
        df_citrus = pd.DataFrame()
    
    try:
        df_coords = pd.read_excel(coords_path)
    except FileNotFoundError:
        st.error(f"파일을 찾을 수 없습니다: {coords_path}")
        df_coords = pd.DataFrame()

    pest_dfs = []
    for p_path in pest_info_paths:
        try:
            pest_dfs.append(pd.read_csv(p_path, encoding='utf-8-sig'))
        except FileNotFoundError:
            st.warning(f"병해충 정보 파일을 찾을 수 없습니다: {p_path}")
    df_pest = pd.concat(pest_dfs, ignore_index=True) if pest_dfs else pd.DataFrame()
    
    return df_weather, df_citrus, df_coords, df_pest

df_weather_raw, df_citrus_raw, df_coords_raw, df_pest = load_data()


# --- 데이터 전처리 ---
# df_weather 전처리
if not df_weather_raw.empty:
    df_weather = df_weather_raw.copy()
    try:
        df_weather['일시'] = pd.to_datetime(df_weather['일시'] + '-01', errors='coerce')
    except TypeError:
        df_weather['일시'] = pd.to_datetime(df_weather['일시'], errors='coerce')
    df_weather['월'] = df_weather['일시'].dt.month
    df_weather['연도'] = df_weather['일시'].dt.year
    df_weather = df_weather.rename(columns={'지점명': '읍면동_기상관측소'})
    if '읍면동_기상관측소' in df_weather.columns:
        df_weather['읍면동_기상관측소'] = df_weather['읍면동_기상관측소'].astype(str).str.strip().str.replace(' ', '')
else:
    df_weather = pd.DataFrame()

# df_coords 전처리
if not df_coords_raw.empty:
    df_coords = df_coords_raw.copy()
    df_coords = df_coords.rename(columns={'행정구역(읍면동)': '읍면동'})
    if '읍면동' in df_coords.columns:
        df_coords.dropna(subset=['읍면동'], inplace=True)
        df_coords['읍면동'] = df_coords['읍면동'].astype(str).str.strip().str.replace(' ', '')
else:
    df_coords = pd.DataFrame()

# df_citrus 전처리
if not df_citrus_raw.empty:
    df_citrus = df_citrus_raw.copy()
    df_citrus = df_citrus.rename(columns={'행정구역(읍면동)': '읍면동'})
    if '읍면동' in df_citrus.columns:
        df_citrus['읍면동'] = df_citrus['읍면동'].astype(str).str.strip().str.replace(' ', '')
    prod_cols = ['노지온주(극조생)', '노지온주(조생)', '노지온주(보통)', '하우스감귤(조기출하)', '비가림(월동)감귤', '만감류(시설)', '만감류(노지)']
    existing_prod_cols = [col for col in prod_cols if col in df_citrus.columns]
    if existing_prod_cols:
        df_citrus['총재배량(톤)'] = df_citrus[existing_prod_cols].sum(axis=1, numeric_only=True)
    else:
        df_citrus['총재배량(톤)'] = 0
else:
    df_citrus = pd.DataFrame()

# --- 읍면동-기상관측소 매핑 (★★★ 사용자 정의 필요 ★★★) ---
읍면동_기상관측소_매핑 = {
    '애월읍': '제주시', '한림읍': '고산', '한경면': '고산', '조천읍': '제주시', '구좌읍': '성산',
    '남원읍': '서귀포시', '성산읍': '성산', '안덕면': '고산', '대정읍': '고산', '표선면': '성산',
    '일도1동': '제주시', '일도2동': '제주시', # ... 기타 모든 읍면동에 대한 매핑
}
if not df_coords.empty and '읍면동' in df_coords.columns:
    for umd in df_coords['읍면동'].dropna().unique():
        if umd not in 읍면동_기상관측소_매핑:
            읍면동_기상관측소_매핑[umd] = '제주시' # 기본값


# --- 사이드바 사용자 선택 ---
st.sidebar.header("조회 조건 설정")

# 적합한 시기 자동 추천 필터
top_suggestions_display = ["수동 선택"] # 기본 옵션
top_suggestions_values = {} # 추천 값 저장을 위한 딕셔너리 (연도, 월)

if not df_weather.empty:
    # 읍면동별로 적합도 계산하지 않고, 각 기상관측소의 월별 데이터를 기준으로 함
    df_weather_suitability = df_weather.copy()
    # 적합도 계산 (이전과 동일한 기준 사용, 필요시 수정)
    df_weather_suitability['기온적합'] = df_weather_suitability['평균기온(°C)'].apply(lambda x: 1 if pd.notnull(x) and 15 <= x <= 25 else 0)
    df_weather_suitability['습도적합'] = df_weather_suitability['평균상대습도(%)'].apply(lambda x: 1 if pd.notnull(x) and 60 <= x <= 80 else 0)
    df_weather_suitability['강수적합'] = df_weather_suitability['월합강수량(00~24h만)(mm)'].apply(lambda x: 1 if pd.notnull(x) and 50 <= x <= 200 else 0)
    df_weather_suitability['풍속적합'] = df_weather_suitability['평균풍속(m/s)'].apply(lambda x: 1 if pd.notnull(x) and x <= 3.4 else 0)
    df_weather_suitability['일조적합'] = df_weather_suitability['합계 일조시간(hr)'].apply(lambda x: 1 if pd.notnull(x) and x >= 150 else 0) # 월 150시간 이상 예시

    df_weather_suitability['적합도점수'] = df_weather_suitability[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
    # 각 관측소별로 해당 월이 '적합'했는지 여부 (점수 기준은 예시)
    df_weather_suitability['월별결과'] = df_weather_suitability['적합도점수'].apply(lambda x: '적합' if x >= 4 else '부적합') # '보통' 제외하고 단순화

    # 연도/월별 '적합' 판정 건수 (관측소 기준)
    if '월별결과' in df_weather_suitability.columns:
        summary = df_weather_suitability[df_weather_suitability['월별결과'] == '적합'].groupby(['연도', '월']).size().reset_index(name='적합관측소수')
        summary = summary.sort_values(by='적합관측소수', ascending=False)
        top_5_summary = summary.head(5)

        for i, row in top_5_summary.iterrows():
            display_text = f"{int(row['연도'])}년 {int(row['월'])}월 (적합 관측소 {row['적합관측소수']}곳)"
            top_suggestions_display.append(display_text)
            top_suggestions_values[display_text] = (int(row['연도']), int(row['월']))
    else:
        st.sidebar.warning("적합도 계산에 필요한 컬럼이 부족하여 추천 시기를 생성할 수 없습니다.")


selected_recommendation = st.sidebar.selectbox(
    "추천 시기 선택 (적합도 기반)",
    top_suggestions_display
)

# 수동 선택 옵션
st.sidebar.markdown("---")
st.sidebar.markdown("##### 또는, 수동으로 연도/월 선택:")
available_years = []
if not df_citrus.empty and '연도' in df_citrus.columns:
    available_years = sorted(df_citrus['연도'].unique(), reverse=True)

manual_selected_year = st.sidebar.selectbox(
    "기준 연도 (수동)", available_years, index=0 if available_years else -1, disabled=(not available_years)
)
manual_selected_month = st.sidebar.selectbox("기준 월 (수동)", list(range(1, 13)))

# 최종 선택된 연도/월 결정
if selected_recommendation != "수동 선택" and selected_recommendation in top_suggestions_values:
    selected_year, selected_month = top_suggestions_values[selected_recommendation]
    st.sidebar.info(f"✅ 추천 시기: {selected_year}년 {selected_month}월 기준으로 표시합니다.")
else:
    selected_year = manual_selected_year
    selected_month = manual_selected_month
    if selected_year is not None : # 수동 선택 시에도 연도가 유효한 경우에만 메시지 표시
         st.sidebar.info(f"✅ 수동 선택: {selected_year}년 {selected_month}월 기준으로 표시합니다.")


# --- 데이터 필터링 및 집계 ---
# (이전 코드의 데이터 필터링 및 집계 로직을 여기에 그대로 사용, 단 selected_year와 selected_month는 위에서 결정된 값 사용)
df_merge = pd.DataFrame()
if not df_weather.empty and not df_citrus.empty and not df_coords.empty and selected_year is not None:
    df_weather_sel = df_weather[(df_weather['연도'] == selected_year) & (df_weather['월'] == selected_month)].copy()
    
    if not df_weather_sel.empty:
        df_weather_agg = df_weather_sel.groupby('읍면동_기상관측소').agg(
            평균기온_월=('평균기온(°C)', 'mean'),
            평균습도_월=('평균상대습도(%)', 'mean'),
            총강수량_월=('월합강수량(00~24h만)(mm)', 'first'),
            평균풍속_월=('평균풍속(m/s)', 'mean'),
            총일조시간_월=('합계 일조시간(hr)', 'first')
        ).reset_index()

        df_citrus_sel = df_citrus[df_citrus['연도'] == selected_year].copy()
        df_citrus_agg = df_citrus_sel.groupby('읍면동')['총재배량(톤)'].sum().reset_index()
        
        df_merge = df_coords[['읍면동', '위도', '경도']].copy()
        df_merge['읍면동_기상관측소'] = df_merge['읍면동'].map(읍면동_기상관측소_매핑)
        df_merge = pd.merge(df_merge, df_weather_agg, on='읍면동_기상관측소', how='left')
        df_merge = pd.merge(df_merge, df_citrus_agg, on='읍면동', how='left')

        # 적합도 계산 (이전에 정의된 df_weather_suitability의 컬럼들을 사용해도 됨)
        # 여기서는 간결성을 위해 다시 계산
        df_merge['기온적합'] = df_merge['평균기온_월'].apply(lambda x: 1 if pd.notnull(x) and 15 <= x <= 25 else 0)
        df_merge['습도적합'] = df_merge['평균습도_월'].apply(lambda x: 1 if pd.notnull(x) and 60 <= x <= 80 else 0)
        df_merge['강수적합'] = df_merge['총강수량_월'].apply(lambda x: 1 if pd.notnull(x) and 50 <= x <= 200 else 0)
        df_merge['풍속적합'] = df_merge['평균풍속_월'].apply(lambda x: 1 if pd.notnull(x) and x <= 3.4 else 0)
        df_merge['일조적합'] = df_merge['총일조시간_월'].apply(lambda x: 1 if pd.notnull(x) and x >= 150 else 0)

        df_merge['적합도점수'] = df_merge[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
        df_merge['결과'] = df_merge['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('보통' if x >= 2 else '부적합'))
    else:
        st.warning(f"{selected_year}년 {selected_month}월에 해당하는 기상 데이터가 없습니다.")


# --- 적합도 결과 필터 (사이드바) ---
st.sidebar.markdown("---")
filter_options_multiselect = st.sidebar.multiselect( # 변수명 변경
    "지도/테이블 표시 필터",
    options=['적합', '보통', '부적합'],
    default=['적합', '보통', '부적합']
)

df_filtered_map = df_merge.copy()
if filter_options_multiselect:
    df_filtered_map = df_merge[df_merge['결과'].isin(filter_options_multiselect)]
else: # 아무것도 선택 안하면 아무것도 안나오도록 (또는 전체)
    df_filtered_map = pd.DataFrame() # 빈 DF로 설정하여 아무것도 표시 안함 (또는 df_merge.copy()로 전체 표시)


# --- 지도 시각화 ---
st.subheader(f"🗺️ {selected_year if selected_year else 'N/A'}년 {selected_month}월 재배 적합도")
# ... (이전 지도 시각화 코드와 동일, 단 df_filtered_map 사용) ...
if not df_filtered_map.empty:
    map_center = [33.361667, 126.528333]
    valid_coords = df_filtered_map.dropna(subset=['위도', '경도'])
    if not valid_coords.empty:
        map_center = [valid_coords['위도'].mean(), valid_coords['경도'].mean()]

    m = folium.Map(location=map_center, zoom_start=10)
    for _, row in df_filtered_map.iterrows():
        if pd.notnull(row.get('위도')) and pd.notnull(row.get('경도')):
            color = 'green' if row.get('결과') == '적합' else ('orange' if row.get('결과') == '보통' else 'red')
            popup_html = f"""
            <b>{row['읍면동']} ({selected_year}년 {selected_month}월)</b><br>
            결과: <b>{row['결과']}</b> (점수: {row.get('적합도점수', 'N/A')}/5)<br>
            <hr style='margin: 2px 0;'>
            기온: {row.get('평균기온_월', 'N/A'):.1f}°C ({row.get('기온적합',0)}) | 습도: {row.get('평균습도_월', 'N/A'):.1f}% ({row.get('습도적합',0)})<br>
            강수: {row.get('총강수량_월', 'N/A'):.1f}mm ({row.get('강수적합',0)}) | 풍속: {row.get('평균풍속_월', 'N/A'):.1f}m/s ({row.get('풍속적합',0)})<br>
            일조: {row.get('총일조시간_월', 'N/A'):.1f}hr ({row.get('일조적합',0)})<br>
            <hr style='margin: 2px 0;'>
            총재배량({selected_year}년): {row.get('총재배량(톤)', 'N/A'):.1f} 톤
            """ # 재배량 포맷 수정
            folium.CircleMarker(
                location=[row['위도'], row['경도']],
                radius=max(5, row.get('적합도점수', 0) * 2 + 5),
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(folium.Html(popup_html, script=True), max_width=350),
                tooltip=f"{row['읍면동']}: {row.get('결과')}"
            ).add_to(m)
    st_folium(m, width=1000, height=600)
else:
    if not df_merge.empty and filter_options_multiselect: # df_merge는 있는데 필터 결과가 없을 때
        st.info(f"선택하신 필터 '{', '.join(filter_options_multiselect)}'에 해당하는 지역이 없습니다.")
    elif df_merge.empty : # 원본 df_merge 자체가 비었을 때
        st.info("지도에 표시할 데이터가 없습니다. 선택한 연도/월의 데이터가 없거나, 데이터 로딩에 실패했습니다.")

# --- 병해충 방제약 정보 ---
st.subheader("🐛 병해충 방제약 정보")
# ... (이전 병해충 정보 코드와 동일) ...
if not df_pest.empty:
    # 사용자가 특정 작물 또는 병해충으로 필터링할 수 있도록 selectbox 추가 가능
    # 예시: df_pest에 '구분'(작물 분류) 컬럼이 있다고 가정
    unique_crops_pest = []
    if '구분' in df_pest.columns:
        unique_crops_pest = df_pest['구분'].dropna().unique()
    
    selected_crop_for_pest = st.selectbox(
        "작물 선택 (병해충 정보)", 
        ["전체"] + list(unique_crops_pest) if unique_crops_pest else ["전체"], # unique_crops_pest가 비어있을 경우 처리
        key="pest_crop_select" # 고유키 추가
    )

    filtered_pest_df = df_pest.copy()
    if selected_crop_for_pest != "전체" and '구분' in filtered_pest_df.columns:
        filtered_pest_df = df_pest[df_pest['구분'] == selected_crop_for_pest]
    
    # 실제 병해충 정보 파일의 컬럼명으로 수정 필요
    display_pest_cols = ['구분', '중점방제대상', '병해충', '방제약', '데이터기준일자'] 
    existing_pest_cols = [col for col in display_pest_cols if col in filtered_pest_df.columns]
    
    if existing_pest_cols:
        st.dataframe(filtered_pest_df[existing_pest_cols])
    else:
        st.warning("병해충 정보 파일에서 주요 컬럼을 찾을 수 없습니다. 로드된 전체 데이터를 표시합니다.")
        st.dataframe(filtered_pest_df)
else:
    st.warning("병해충 데이터를 불러오지 못했습니다.")
