import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="제주 농부 스마트 대시보드", layout="wide", page_icon="🍊")

# --- 데이터 로딩 함수 (이전과 동일) ---
@st.cache_data
def load_data(db_file, citrus_file_path, coords_file_path, pest_info_files_paths):
    # ... (이전 load_data 함수 내용 전체 복사) ...
    df_weather, df_citrus, df_coords = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    df_pest_all_info = pd.DataFrame()

    # 1. 기상 데이터 (DB)
    if not os.path.exists(db_file):
        st.error(f"DB 파일을 찾을 수 없습니다: {db_file}")
    else:
        conn = sqlite3.connect(db_file)
        try:
            df_weather = pd.read_sql("SELECT * FROM asos_weather", conn) # 실제 테이블명 확인 필요
            if not df_weather.empty:
                df_weather['일시'] = pd.to_datetime(df_weather['일시'] + '-01', errors='coerce')
                df_weather['월'] = df_weather['일시'].dt.month
                df_weather['연도'] = df_weather['일시'].dt.year
                df_weather = df_weather.rename(columns={'지점명': '읍면동_기상관측소'})
                df_weather['읍면동_기상관측소'] = df_weather['읍면동_기상관측소'].str.strip().str.replace(' ', '')
        except Exception as e:
            st.error(f"기상 데이터 로드/처리 오류: {e}")
            df_weather = pd.DataFrame()
        conn.close()

    # 2. 재배량 데이터 (Excel)
    try:
        df_citrus = pd.read_excel(citrus_file_path)
        if '행정구역(읍면동)' in df_citrus.columns:
            df_citrus = df_citrus.rename(columns={'행정구역(읍면동)': '읍면동'})
        df_citrus['읍면동'] = df_citrus['읍면동'].str.strip().str.replace(' ', '')
        citrus_prod_cols = ['노지온주(극조생)', '노지온주(조생)', '노지온주(보통)',
                            '하우스감귤(조기출하)', '비가림(월동)감귤', '만감류(시설)', '만감류(노지)']
        existing_prod_cols = [col for col in citrus_prod_cols if col in df_citrus.columns]
        if existing_prod_cols:
            df_citrus['총재배량(톤)'] = df_citrus[existing_prod_cols].sum(axis=1, numeric_only=True)
        else:
            df_citrus['총재배량(톤)'] = 0
    except FileNotFoundError:
        st.error(f"파일을 찾을 수 없습니다: {citrus_file_path}")
    except Exception as e:
        st.error(f"감귤 재배량 데이터 처리 오류: {e}")
        df_citrus = pd.DataFrame()

    # 3. 좌표 데이터 (Excel)
    try:
        df_coords = pd.read_excel(coords_file_path)
        if '행정구역(읍면동)' in df_coords.columns:
            df_coords = df_coords.rename(columns={'행정구역(읍면동)': '읍면동'})
        df_coords['읍면동'] = df_coords['읍면동'].str.strip().str.replace(' ', '')
    except FileNotFoundError:
        st.error(f"파일을 찾을 수 없습니다: {coords_file_path}")
    except Exception as e:
        st.error(f"좌표 데이터 처리 오류: {e}")
        df_coords = pd.DataFrame()

    # 4. 병해충 정보 데이터 (CSV)
    pest_dfs = []
    for file_path in pest_info_files_paths:
        try:
            df_temp_pest = pd.read_csv(file_path, encoding='utf-8-sig')
            pest_dfs.append(df_temp_pest)
        except FileNotFoundError:
            st.warning(f"병해충 정보 파일을 찾을 수 없습니다: {file_path}")
        except Exception as e:
            st.warning(f"병해충 정보 파일 ({file_path}) 처리 오류: {e}")
    if pest_dfs:
        df_pest_all_info = pd.concat(pest_dfs, ignore_index=True)

    return df_weather, df_citrus, df_coords, df_pest_all_info


# --- 파일 경로 설정 ---
BASE_DIR = 'data'
DB_PATH = os.path.join(BASE_DIR, 'asos_weather.db')
CITRUS_DATA_PATH = os.path.join(BASE_DIR, '5.xlsx')
COORDS_PATH = os.path.join(BASE_DIR, 'coords.xlsx')
PEST_INFO_PATHS = [
    os.path.join(BASE_DIR, 'pest_disease_info_1.csv'),
    os.path.join(BASE_DIR, 'pest_disease_info_2.csv'),
    os.path.join(BASE_DIR, 'pest_disease_info_3.csv')
]

# --- 앱 시작 ---
st.title("🍊 제주 농부 스마트 대시보드")
st.markdown("제주도 농사에 필요한 모든 정보를 한 곳에서 확인하세요.")

# 데이터 로딩 실행
df_weather, df_citrus, df_coords, df_pest_info = load_data(DB_PATH, CITRUS_DATA_PATH, COORDS_PATH, PEST_INFO_PATHS)

# --- 사용자 입력 ---
available_years = []
if not df_citrus.empty and '연도' in df_citrus.columns:
    available_years = sorted(df_citrus['연도'].unique(), reverse=True)

selected_year = st.sidebar.selectbox(
    "기준 연도를 선택하세요",
    available_years,
    index=0 if available_years else -1,
    disabled=(not available_years)
)
selected_month = st.sidebar.selectbox("확인할 월을 선택하세요", list(range(1, 13)))

# --- 읍면동-기상관측소 매핑 (예시 - 실제 상황에 맞게 수정 필요) ---
읍면동_기상관측소_매핑 = {
    '애월읍': '제주시', '한림읍': '고산', '한경면': '고산', '조천읍': '제주시', '구좌읍': '성산',
    '남원읍': '서귀포시', '성산읍': '성산', '안덕면': '고산', '대정읍': '고산', '표선면': '성산',
    # 제주시 동지역 추가 (예시)
    '일도1동': '제주시', '일도2동': '제주시', '이도1동': '제주시', '이도2동': '제주시',
    '삼도1동': '제주시', '삼도2동': '제주시', '용담1동': '제주시', '용담2동': '제주시',
    '건입동': '제주시', '화북동': '제주시', '삼양동': '제주시', '봉개동': '제주시',
    '아라동': '제주시', '오라동': '제주시', '연동': '제주시', '노형동': '제주시',
    '외도동': '제주시', '이호동': '제주시', '도두동': '제주시',
    # 서귀포시 동지역 추가 (예시)
    '송산동': '서귀포시', '정방동': '서귀포시', '중앙동': '서귀포시', '천지동': '서귀포시',
    '효돈동': '서귀포시', '영천동': '서귀포시', '동홍동': '서귀포시', '서홍동': '서귀포시',
    '대륜동': '서귀포시', '대천동': '서귀포시', '중문동': '서귀포시', '예래동': '서귀포시'
}
if not df_coords.empty:
    for umd in df_coords['읍면동'].unique():
        if umd not in 읍면동_기상관측소_매핑:
            # 매핑되지 않은 읍면동은 가장 가까운 관측소를 찾거나 기본값 설정 (여기서는 '제주시'로)
            st.warning(f"'{umd}'에 대한 기상관측소 매핑 정보가 없습니다. 기본값('제주시')을 사용합니다.")
            읍면동_기상관측소_매핑[umd] = '제주시'


# --- 데이터 처리 및 병합 ---
df_display = pd.DataFrame() # 최종적으로 지도 및 테이블에 표시될 데이터

if not df_weather.empty and not df_citrus.empty and not df_coords.empty and selected_year is not None:
    df_weather_selected = df_weather[(df_weather['연도'] == selected_year) & (df_weather['월'] == selected_month)].copy()
    
    if not df_weather_selected.empty:
        df_weather_agg = df_weather_selected.groupby('읍면동_기상관측소').agg(
            평균기온_월=('평균기온(°C)', 'mean'),
            평균습도_월=('평균상대습도(%)', 'mean'),
            총강수량_월=('월합강수량(00~24h만)(mm)', 'first'),
            평균풍속_월=('평균풍속(m/s)', 'mean'),
            총일조시간_월=('합계 일조시간(hr)', 'first')
        ).reset_index()

        df_citrus_selected_year = df_citrus[df_citrus['연도'] == selected_year].copy()
        df_citrus_agg = df_citrus_selected_year.groupby('읍면동')['총재배량(톤)'].sum().reset_index()
        
        df_display = df_coords[['읍면동', '위도', '경도']].copy()
        df_display['읍면동_기상관측소'] = df_display['읍면동'].map(읍면동_기상관측소_매핑)
        df_display = pd.merge(df_display, df_weather_agg, on='읍면동_기상관측소', how='left')
        df_display = pd.merge(df_display, df_citrus_agg, on='읍면동', how='left')

        # 적합도 계산
        df_display['기온적합'] = df_display['평균기온_월'].apply(lambda x: 1 if pd.notnull(x) and 15 <= x <= 25 else 0)
        df_display['습도적합'] = df_display['평균습도_월'].apply(lambda x: 1 if pd.notnull(x) and 60 <= x <= 80 else 0)
        df_display['강수적합'] = df_display['총강수량_월'].apply(lambda x: 1 if pd.notnull(x) and 50 <= x <= 200 else 0)
        df_display['풍속적합'] = df_display['평균풍속_월'].apply(lambda x: 1 if pd.notnull(x) and x <= 3.4 else 0)
        df_display['일조적합'] = df_display['총일조시간_월'].apply(lambda x: 1 if pd.notnull(x) and x >= 150 else 0)
        df_display['적합도점수'] = df_display[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
        df_display['결과'] = df_display['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('보통' if x >= 2 else '부적합'))
    else:
        st.warning(f"{selected_year}년 {selected_month}월에 해당하는 기상 데이터가 없습니다.")

# --- 적합도 결과 필터링 ---
st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ 지역 필터")
filter_options = ['전체 보기', '적합', '보통', '부적합']
selected_filter = st.sidebar.multiselect(
    "적합도 결과로 지역 필터링",
    options=filter_options[1:], # '전체 보기' 제외
    default=[] # 기본값은 선택 없음 (전체 보기)
)

df_filtered_display = df_display.copy() # 필터링을 위한 복사본
if selected_filter: # 사용자가 필터를 선택한 경우
    df_filtered_display = df_display[df_display['결과'].isin(selected_filter)]


# --- 지도 시각화 ---
st.subheader(f"🗺️ {selected_year if selected_year else ''}년 {selected_month}월 읍면동별 감귤 재배 적합도")
if not df_filtered_display.empty: # 필터링된 데이터로 지도 생성
    map_center = [33.361667, 126.528333]
    valid_coords_df = df_filtered_display.dropna(subset=['위도', '경도'])
    if not valid_coords_df.empty:
        map_center = [valid_coords_df['위도'].mean(), valid_coords_df['경도'].mean()]

    m = folium.Map(location=map_center, zoom_start=10)
    for _, row in df_filtered_display.iterrows(): # 필터링된 데이터 사용
        if pd.notnull(row.get('위도')) and pd.notnull(row.get('경도')):
            color = 'green' if row['결과'] == '적합' else ('orange' if row['결과'] == '보통' else 'red')
            popup_html = f"""
            <b>{row['읍면동']} ({selected_year}년 {selected_month}월)</b><br>
            결과: <b>{row['결과']}</b> (점수: {row.get('적합도점수', 'N/A')}/5)<br>
            <hr style='margin: 2px 0;'>
            기온: {row.get('평균기온_월', 'N/A'):.1f}°C ({row.get('기온적합',0)}) | 습도: {row.get('평균습도_월', 'N/A'):.1f}% ({row.get('습도적합',0)})<br>
            강수: {row.get('총강수량_월', 'N/A'):.1f}mm ({row.get('강수적합',0)}) | 풍속: {row.get('평균풍속_월', 'N/A'):.1f}m/s ({row.get('풍속적합',0)})<br>
            일조: {row.get('총일조시간_월', 'N/A'):.1f}hr ({row.get('일조적합',0)})<br>
            <hr style='margin: 2px 0;'>
            총재배량({selected_year}년): {row.get('총재배량(톤)', 'N/A'):.1f} 톤
            """
            folium.CircleMarker(
                location=[row['위도'], row['경도']],
                radius=max(5, row.get('적합도점수', 0) * 2 + 5),
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(folium.Html(popup_html, script=True), max_width=350),
                tooltip=f"{row['읍면동']}: {row['결과']}"
            ).add_to(m)
    st_folium(m, width=1000, height=600)
else:
    if not df_display.empty and selected_filter:
        st.info(f"선택하신 필터 '{', '.join(selected_filter)}'에 해당하는 지역이 없습니다.")
    elif df_display.empty:
        st.info("지도에 표시할 데이터가 없습니다. 연도와 월을 확인해주세요.")


# --- 필터링된 지역 목록 테이블 ---
if not df_filtered_display.empty:
    st.subheader(f"🔎 필터링된 지역 목록 ({', '.join(selected_filter) if selected_filter else '전체'})")
    display_cols_table = ['읍면동', '결과', '적합도점수', '평균기온_월', '평균습도_월', '총강수량_월', '평균풍속_월', '총일조시간_월', '총재배량(톤)']
    # 컬럼 존재 여부 확인 후 표시
    existing_display_cols = [col for col in display_cols_table if col in df_filtered_display.columns]
    st.dataframe(df_filtered_display[existing_display_cols].sort_values(by='적합도점수', ascending=False).reset_index(drop=True))
elif df_display.empty and selected_filter : # 필터를 선택했지만 원본 데이터 자체가 없는 경우
     st.info(f"선택하신 필터 '{', '.join(selected_filter)}'에 해당하는 지역이 없습니다 (원본 데이터 부족).")
elif not df_display.empty and selected_filter: # 필터는 있지만 결과가 없는 경우
    st.info(f"선택하신 필터 '{', '.join(selected_filter)}'에 해당하는 지역이 없습니다.")


# --- 병해충 방제약 정보 ---
# ... (이전과 동일) ...
st.subheader("🐛 주요 병해충 방제약 정보")
if not df_pest_info.empty:
    display_pest_cols = ['구분', '중점방제대상', '병해충', '방제약', '데이터기준일자']
    existing_pest_cols = [col for col in display_pest_cols if col in df_pest_info.columns]
    if existing_pest_cols:
        st.dataframe(df_pest_info[existing_pest_cols])
    else:
        st.warning("병해충 정보 파일에서 주요 컬럼을 찾을 수 없습니다. 전체 데이터를 표시합니다.")
        st.dataframe(df_pest_info)
else:
    st.warning("병해충 정보 파일을 로드하지 못했습니다.")
