import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="제주 농부 스마트 대시보드", layout="wide", page_icon="🍊")

# --- 데이터 로딩 함수 (캐싱 적용) ---
@st.cache_data
def load_data(db_file, citrus_file_path, coords_file_path, pest_info_files_paths):
    df_weather, df_citrus, df_coords = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    df_pest_all_info = pd.DataFrame()

    # 1. 기상 데이터 (DB)
    if not os.path.exists(db_file):
        st.error(f"DB 파일을 찾을 수 없습니다: {db_file}")
    else:
        conn = sqlite3.connect(db_file)
        try:
            # DB에 있는 실제 테이블명으로 변경해야 함 (예: 'asos_weather')
            df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
            if not df_weather.empty:
                df_weather['일시'] = pd.to_datetime(df_weather['일시'] + '-01', errors='coerce') # 'YYYY-MM' 형식 가정
                df_weather['월'] = df_weather['일시'].dt.month
                df_weather['연도'] = df_weather['일시'].dt.year
                df_weather = df_weather.rename(columns={'지점명': '읍면동_기상관측소'}) # 원본 지점명 유지 후 매핑
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
BASE_DIR = 'data' # 데이터 폴더를 지정
DB_PATH = os.path.join(BASE_DIR, 'asos_weather.db')
CITRUS_DATA_PATH = os.path.join(BASE_DIR, '5.xlsx') # (pest_disease_5.csv 와 유사한 내용으로 가정)
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
# 연도 선택 (df_citrus에 '연도' 컬럼이 있다고 가정)
available_years = []
if not df_citrus.empty and '연도' in df_citrus.columns:
    available_years = sorted(df_citrus['연도'].unique(), reverse=True)

selected_year = st.selectbox("기준 연도를 선택하세요", available_years, index=0 if available_years else -1,
                             disabled=(not available_years)) # 데이터 없으면 비활성화
selected_month = st.selectbox("확인할 월을 선택하세요", list(range(1, 13)))


# --- 읍면동-기상관측소 매핑 (예시 - 실제 상황에 맞게 수정 필요) ---
# 이 매핑은 매우 중요합니다. 실제 읍면동과 가장 관련 있는 기상관측소를 연결해야 합니다.
# 예를 들어, '애월읍'은 '제주시' 관측소 데이터를 사용한다고 가정.
# 좀 더 정확한 방법은 읍면동별로 가장 가까운 관측소를 찾거나, 전문가의 의견을 반영하는 것입니다.
읍면동_기상관측소_매핑 = {
    '애월읍': '제주시', '한림읍': '고산', '한경면': '고산', '조천읍': '제주시', '구좌읍': '성산', # 제주시 예시
    '남원읍': '서귀포시', '성산읍': '성산', '안덕면': '고산', '대정읍': '고산', '표선면': '성산'  # 서귀포시 예시
    # ... 나머지 읍면동에 대한 매핑 추가 ...
}
# df_coords 또는 df_citrus의 모든 읍면동에 대해 기본 매핑 (가장 가까운 관측소 등으로 대체 가능)
if not df_coords.empty:
    for umd in df_coords['읍면동'].unique():
        if umd not in 읍면동_기상관측소_매핑:
            읍면동_기상관측소_매핑[umd] = '제주시' # 기본값 또는 다른 로직으로 설정

# --- 데이터 처리 및 병합 ---
df_display = pd.DataFrame()

if not df_weather.empty and not df_citrus.empty and not df_coords.empty and selected_year is not None:
    # 1. 선택 연도/월 기상 데이터 집계
    df_weather_selected = df_weather[(df_weather['연도'] == selected_year) & (df_weather['월'] == selected_month)].copy()
    
    if not df_weather_selected.empty:
        # 기상관측소명을 실제 읍면동명과 연결하기 위한 컬럼 추가
        df_weather_selected['읍면동'] = df_weather_selected['읍면동_기상관측소'].map(
            {v: k for k, v_list in 읍면동_기상관측소_매핑.items() for v in (v_list if isinstance(v_list, list) else [v_list])}
        ) # 이 부분은 매핑 방식에 따라 수정 필요. 간단하게는 관측소명 자체를 key로 사용할 수도 있음.
           # 지금은 모든 읍면동이 하나의 관측소에 매핑된다고 가정하고 단순화 필요.

        # 각 기상관측소의 월 데이터를 사용 (이미 월별 데이터이므로 추가 집계 시 주의)
        # 동일 '읍면동_기상관측소'에 여러 해의 데이터가 있을 수 있으므로, 여기서는 해당 연월의 값만 사용.
        df_weather_agg = df_weather_selected.groupby('읍면동_기상관측소').agg(
            평균기온_월=('평균기온(°C)', 'mean'),        # 해당 연월 값이므로 mean, first, last 등 동일
            평균습도_월=('평균상대습도(%)', 'mean'),
            총강수량_월=('월합강수량(00~24h만)(mm)', 'first'), # 이미 월합계
            평균풍속_월=('평균풍속(m/s)', 'mean'),
            총일조시간_월=('합계 일조시간(hr)', 'first')  # 이미 월합계
        ).reset_index()

        # 2. 선택 연도 감귤 데이터
        df_citrus_selected_year = df_citrus[df_citrus['연도'] == selected_year].copy()
        df_citrus_agg = df_citrus_selected_year.groupby('읍면동')['총재배량(톤)'].sum().reset_index()

        # 3. 병합 (읍면동명 기준으로)
        # 먼저, 좌표 데이터를 기준으로 df_display 생성
        df_display = df_coords[['읍면동', '위도', '경도']].copy()
        
        # 읍면동에 해당하는 기상관측소명 컬럼 추가
        df_display['읍면동_기상관측소'] = df_display['읍면동'].map(읍면동_기상관측소_매핑)
        
        # 기상 데이터 병합 (읍면동_기상관측소 기준)
        df_display = pd.merge(df_display, df_weather_agg, on='읍면동_기상관측소', how='left')
        
        # 감귤 재배량 데이터 병합 (읍면동 기준)
        df_display = pd.merge(df_display, df_citrus_agg, on='읍면동', how='left')

        # 누락된 읍면동 확인
        if '읍면동_기상관측소' in df_display.columns:
            missing_coords_count = df_display['위도'].isna().sum()
            st.write(f"🗺️ 병합 후 좌표 누락 건수: {missing_coords_count} (좌표 파일에 해당 읍면동이 없거나, 병합 키 불일치)")
            missing_weather_count = df_display['평균기온_월'].isna().sum() # 대표적인 기상 컬럼으로 확인
            st.write(f"🌦️ 병합 후 기상 데이터 누락 건수: {missing_weather_count} (기상 데이터에 해당 관측소가 없거나, 매핑 오류)")


        # 4. 적합도 계산 (기준값은 전문가 자문 필요)
        df_display['기온적합'] = df_display['평균기온_월'].apply(lambda x: 1 if pd.notnull(x) and 15 <= x <= 25 else 0)
        df_display['습도적합'] = df_display['평균습도_월'].apply(lambda x: 1 if pd.notnull(x) and 60 <= x <= 80 else 0)
        df_display['강수적합'] = df_display['총강수량_월'].apply(lambda x: 1 if pd.notnull(x) and 50 <= x <= 200 else 0) # 월 50~200mm
        df_display['풍속적합'] = df_display['평균풍속_월'].apply(lambda x: 1 if pd.notnull(x) and x <= 3.4 else 0) # 3.4m/s 이하 (약풍)
        df_display['일조적합'] = df_display['총일조시간_월'].apply(lambda x: 1 if pd.notnull(x) and x >= 150 else 0) # 월 150시간 이상

        df_display['적합도점수'] = df_display[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
        df_display['결과'] = df_display['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('보통' if x >= 2 else '부적합')) # 기준 변경
    else:
        st.warning(f"{selected_year}년 {selected_month}월에 해당하는 기상 데이터가 없습니다.")

# --- 지도 시각화 ---
st.subheader(f"🗺️ {selected_year if selected_year else ''}년 {selected_month}월 읍면동별 감귤 재배 적합도")
if not df_display.empty:
    map_center = [33.361667, 126.528333]
    valid_coords_df = df_display.dropna(subset=['위도', '경도'])
    if not valid_coords_df.empty:
        map_center = [valid_coords_df['위도'].mean(), valid_coords_df['경도'].mean()]

    m = folium.Map(location=map_center, zoom_start=10)
    for _, row in df_display.iterrows():
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
                radius=max(5, row.get('적합도점수', 0) * 2 + 5), # 최소 반경 5, 점수 따라 증가
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(folium.Html(popup_html, script=True), max_width=350),
                tooltip=f"{row['읍면동']}: {row['결과']}"
            ).add_to(m)
    st_folium(m, width=1000, height=600)
else:
    st.info("지도에 표시할 데이터가 없습니다. 연도와 월을 확인해주세요.")


# --- 병해충 방제약 정보 ---
st.subheader("🐛 주요 병해충 방제약 정보")
if not df_pest_info.empty:
    display_pest_cols = ['구분', '중점방제대상', '병해충', '방제약', '데이터기준일자'] # 실제 컬럼명에 맞게 수정
    existing_pest_cols = [col for col in display_pest_cols if col in df_pest_info.columns]
    if existing_pest_cols:
        st.dataframe(df_pest_info[existing_pest_cols])
    else:
        st.warning("병해충 정보 파일에서 주요 컬럼을 찾을 수 없습니다. 전체 데이터를 표시합니다.")
        st.dataframe(df_pest_info) # 컬럼 못찾으면 전체 표시
else:
    st.warning("병해충 정보 파일을 로드하지 못했습니다.")
