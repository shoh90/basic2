import streamlit as st
import pandas as pd
import folium
import sqlite3
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(page_title="감귤 재배 적합지 추천", layout="wide", page_icon="🍊")

st.title("🍊 감귤 재배 적합지 추천")
st.markdown("제주도 주요 지역의 감귤 재배량과 재배 적합도를 지도에서 확인하세요.")

# 데이터 로딩
@st.cache_data
def load_data():
    # 데이터베이스 경로는 실제 환경에 맞게 수정해야 할 수 있습니다.
    # 예: 'data/asos_weather.db' -> 'your_project_folder/data/asos_weather.db'
    try:
        conn = sqlite3.connect('data/asos_weather.db')
        df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
    except sqlite3.OperationalError as e:
        st.error(f"asos_weather.db 파일을 찾을 수 없거나 열 수 없습니다: {e}. 'data' 폴더에 파일이 있는지 확인해주세요.")
        st.stop()
    except Exception as e:
        st.error(f"asos_weather 데이터 로딩 중 오류 발생: {e}")
        st.stop()
    finally:
        if 'conn' in locals() and conn:
            conn.close()

    try:
        df_citrus = pd.read_excel('data/5.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})
    except FileNotFoundError:
        st.error("5.xlsx 파일을 찾을 수 없습니다. 'data' 폴더에 파일이 있는지 확인해주세요.")
        st.stop()
    except Exception as e:
        st.error(f"5.xlsx 데이터 로딩 중 오류 발생: {e}")
        st.stop()

    try:
        df_coords = pd.read_excel('data/coords.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})
    except FileNotFoundError:
        st.error("coords.xlsx 파일을 찾을 수 없습니다. 'data' 폴더에 파일이 있는지 확인해주세요.")
        st.stop()
    except Exception as e:
        st.error(f"coords.xlsx 데이터 로딩 중 오류 발생: {e}")
        st.stop()

    return df_weather, df_citrus, df_coords

df_weather, df_citrus, df_coords = load_data()

# 데이터 전처리
df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['월'] = df_weather['일시'].dt.month
df_weather['연도'] = df_weather['일시'].dt.year

# 총재배량 계산
prod_cols = ['노지온주(극조생)', '노지온주(조생)', '노지온주(보통)', '하우스감귤(조기출하)',
             '비가림(월동)감귤', '만감류(시설)', '만감류(노지)']
# df_citrus에 해당 컬럼들이 모두 있는지 확인 후 합산
existing_prod_cols = [col for col in prod_cols if col in df_citrus.columns]
if not existing_prod_cols:
    st.warning("총재배량 계산에 필요한 컬럼이 df_citrus에 없습니다. 확인해주세요.")
    df_citrus['총재배량(톤)'] = 0
else:
    df_citrus['총재배량(톤)'] = df_citrus[existing_prod_cols].sum(axis=1, numeric_only=True)


# --- 핵심 원인 해결 부분 ---
# df_weather의 '지점명'과 df_citrus/df_coords의 '읍면동' 매칭 문제 해결을 위해
# '읍면동'을 대표 '지점명'으로 매핑합니다.

# 매핑 테이블 (수동 지정, 필요시 보완 가능)
mapping = {
    '애월읍': '제주시', '한림읍': '고산', '한경면': '고산', '조천읍': '제주시',
    '구좌읍': '성산', '남원읍': '서귀포시', '성산읍': '성산', '안덕면': '고산',
    '대정읍': '고산', '표선면': '성산'
    # 여기에 포함되지 않은 읍면동은 아래 .fillna()에 의해 '제주시'로 매핑됩니다.
    # 또는 다른 기본값을 설정하거나, 매핑되지 않는 경우를 따로 처리할 수 있습니다.
}
df_coords['읍면동'] = df_coords['읍면동'].str.strip()
df_citrus['읍면동'] = df_citrus['읍면동'].str.strip()
# --------------------------

# 사용자 입력
if '연도' not in df_citrus.columns:
    st.error("df_citrus에 '연도' 컬럼이 없습니다. 데이터를 확인해주세요.")
    st.stop()

available_years_series = df_citrus['연도'].dropna().unique()
# 연도 데이터가 숫자로 되어 있는지 확인하고, 정수로 변환 (필요시)
try:
    available_years = sorted([int(year) for year in available_years_series], reverse=True)
except ValueError:
    st.error("'연도' 컬럼에 변환할 수 없는 값이 포함되어 있습니다. 데이터를 확인해주세요.")
    available_years = sorted(list(available_years_series), reverse=True) # 원래대로 정렬

if not available_years:
    st.warning("선택 가능한 연도가 없습니다. df_citrus 데이터를 확인해주세요.")
    st.stop()
selected_year = st.selectbox("확인할 연도를 선택하세요", available_years)

# 읍면동 기준 테이블 생성
# df_citrus에서 선택된 연도의 데이터만 필터링
df_citrus_selected_year = df_citrus[df_citrus['연도'] == selected_year]

# df_coords와 df_citrus_selected_year 병합
df_base = df_coords.merge(df_citrus_selected_year[['읍면동', '총재배량(톤)']], on='읍면동', how='left')

# '읍면동'을 '지점명'으로 매핑 (핵심 원인 해결 로직)
df_base['지점명'] = df_base['읍면동'].map(mapping).fillna('제주시') # 매핑되지 않는 경우 '제주시'로 기본값 처리

# 월별 기상데이터 집계
df_weather_year = df_weather[df_weather['연도'] == selected_year]
if df_weather_year.empty:
    st.warning(f"{selected_year}년의 기상 데이터가 없습니다. 다른 연도를 선택하거나 데이터를 확인해주세요.")
    df_weather_agg = pd.DataFrame(columns=['지점명', '평균기온(°C)', '평균상대습도(%)', '월합강수량(00~24h만)(mm)', '평균풍속(m/s)', '합계 일조시간(hr)'])
else:
    df_weather_agg = df_weather_year.groupby('지점명').agg(
        평균기온_C=('평균기온(°C)', 'mean'),
        평균상대습도_perc=('평균상대습도(%)', 'mean'),
        월합강수량_mm=('월합강수량(00~24h만)(mm)', 'sum'), # 연간 총 강수량
        평균풍속_ms=('평균풍속(m/s)', 'mean'),
        합계일조시간_hr=('합계 일조시간(hr)', 'sum')      # 연간 총 일조시간
    ).reset_index()
    # 컬럼명 원복 (편의상 원본 컬럼명 사용)
    df_weather_agg = df_weather_agg.rename(columns={
        '평균기온_C': '평균기온(°C)',
        '평균상대습도_perc': '평균상대습도(%)',
        '월합강수량_mm': '월합강수량(00~24h만)(mm)',
        '평균풍속_ms': '평균풍속(m/s)',
        '합계일조시간_hr': '합계 일조시간(hr)'
    })


# 최종 데이터 병합
df = df_base.merge(df_weather_agg, on='지점명', how='left')

# 적합도 계산 (기상 데이터가 없는 경우를 대비하여 pd.notnull 확인)
# 월합강수량과 합계일조시간은 연간 총량이므로, 적합도 기준을 월평균 기준으로 변경하거나, 연간 기준을 사용해야 합니다.
# 현재 코드는 연간 총량을 사용하고 있으나, 월별 강수량 기준(30~100mm)은 연간 값에 부적합합니다.
# 여기서는 일단 현재 로직을 유지하되, 이 부분에 대한 검토가 필요함을 인지해야 합니다.
# 예시: 연간 강수량 800~1500mm, 연간 일조시간 1800~2500시간 등

# 적합도 기준 재설정 필요:
# 현재 '월합강수량'은 연간 총합, '합계 일조시간'도 연간 총합으로 계산됨.
# 따라서 적합도 기준도 연간 기준으로 변경하거나, 월평균으로 데이터를 다시 가공해야 함.
# 여기서는 일단 기존 로직을 따르되, 주석으로 문제점을 명시함.
# 실제 적용 시에는 이 기준을 현실에 맞게 수정해야 함.

# 연간 강수량 적합도 (예시: 800mm ~ 1500mm)
df['강수적합'] = df['월합강수량(00~24h만)(mm)'].apply(lambda x: 1 if pd.notnull(x) and 800 <= x <= 2000 else 0) # 예시 기준
# 연간 일조시간 적합도 (예시: 1800시간 이상)
df['일조적합'] = df['합계 일조시간(hr)'].apply(lambda x: 1 if pd.notnull(x) and x >= 1800 else 0) # 예시 기준

df['기온적합'] = df['평균기온(°C)'].apply(lambda x: 1 if pd.notnull(x) and 15 <= x <= 20 else 0) # 감귤 생육 적온 (일반적)
df['습도적합'] = df['평균상대습도(%)'].apply(lambda x: 1 if pd.notnull(x) and 60 <= x <= 80 else 0)
df['풍속적합'] = df['평균풍속(m/s)'].apply(lambda x: 1 if pd.notnull(x) and x <= 3 else 0) # 바람이 너무 강하면 안 좋음

df['적합도점수'] = df[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
df['결과'] = df['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('부분적합' if x ==3 else '부적합')) # 기준 세분화

# 지도 시각화
st.subheader(f"🗺️ {selected_year}년 기준 감귤 재배량 및 적합도 지도")

if df.empty or '위도' not in df.columns or '경도' not in df.columns:
    st.warning("지도에 표시할 데이터가 없습니다. 데이터를 확인하거나 다른 연도를 선택해주세요.")
else:
    m = folium.Map(location=[33.37, 126.53], zoom_start=9) # 제주도 중심 및 줌 레벨 조정

    for _, row in df.iterrows():
        if pd.notnull(row['위도']) and pd.notnull(row['경도']):
            color = 'green' if row['결과'] == '적합' else ('orange' if row['결과'] == '부분적합' else 'red')
            
            # NaN 값을 0 또는 '정보 없음'으로 대체
            total_production = row.get('총재배량(톤)')
            total_production_display = f"{total_production:.2f}톤" if pd.notnull(total_production) else "정보 없음"
            
            avg_temp = row.get('평균기온(°C)')
            avg_temp_display = f"{avg_temp:.1f}°C" if pd.notnull(avg_temp) else "N/A"

            popup_html = f"""
            <b>{row['읍면동']} ({row['결과']})</b><br>
            총재배량: {total_production_display}<br>
            평균기온: {avg_temp_display}<br>
            적합도점수: {row['적합도점수']}/5
            """
            folium.CircleMarker(
                location=[row['위도'], row['경도']],
                radius=max(5, min(row.get('총재배량(톤)', 0) / 1000, 15)) if pd.notnull(row.get('총재배량(톤)')) else 5, # 재배량에 따라 원 크기 조정 (최소 5, 최대 15)
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                tooltip=f"{row['읍면동']}",
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(m)

    st_folium(m, width=1000, height=600)

# 적합 지역만 테이블 요약
st.write("📝 지역별 요약 (적합 또는 부분적합)")
# 표시할 컬럼 정의 (결과 및 적합도 점수 추가)
summary_cols = ['읍면동', '결과', '적합도점수', '총재배량(톤)', '평균기온(°C)', '평균상대습도(%)', '월합강수량(00~24h만)(mm)', '평균풍속(m/s)', '합계 일조시간(hr)']
# 데이터프레임에 해당 컬럼이 있는지 확인
existing_summary_cols = [col for col in summary_cols if col in df.columns]

if not df[df['결과'].isin(['적합', '부분적합'])].empty:
    st.dataframe(df[df['결과'].isin(['적합', '부분적합'])][existing_summary_cols].reset_index(drop=True))
else:
    st.write("적합 또는 부분적합으로 평가된 지역이 없습니다.")

st.markdown("""
---
**참고:**
- **매핑 방식:** 읍면동별 기상 데이터 부재로, 각 읍면동을 가장 대표할 수 있는 주요 기상 관측소(제주시, 고산, 성산, 서귀포시)의 데이터로 매핑하여 사용합니다. `mapping` 딕셔너리에 정의되지 않은 읍면동은 '제주시' 관측소 데이터를 기본값으로 사용합니다.
- **적합도 기준:** 기온, 습도, 강수량, 풍속, 일조시간에 대한 일반적인 감귤 재배 적합 기준을 사용하였으며, 이는 실제 환경 및 품종에 따라 달라질 수 있습니다.
  - **강수량 및 일조시간:** 현재 '월합강수량'과 '합계일조시간'은 선택된 연도의 **연간 총량**으로 집계됩니다. 따라서 적합도 기준(예: 연간 강수량 800-2000mm, 연간 일조 1800시간 이상)도 이에 맞게 조정되었습니다.
- **데이터 출처:** ASOS 기상자료, 농산물 생산량 통계(가상), 읍면동 좌표(가상).
""")
