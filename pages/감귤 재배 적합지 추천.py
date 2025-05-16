import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

# --- 페이지 설정 ---
st.set_page_config(page_title="감귤 재배 적합지 추천", layout="wide", page_icon="🍊")

st.title("🍊 감귤 재배 적합지 추천")
st.markdown("제주도 주요 지역의 감귤 재배량과 재배 적합도를 지도를 통해 확인하세요.")

# --- 데이터 로딩 ---
@st.cache_data
def load_data():
    try:
        conn = sqlite3.connect('data/asos_weather.db')
        df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
    except sqlite3.OperationalError as e:
        st.error(f"데이터베이스 오류: {e}. 'data/asos_weather.db' 파일 경로 및 상태를 확인해주세요.")
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
        st.error("'data/5.xlsx' 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
        st.stop()
    except Exception as e:
        st.error(f"5.xlsx 데이터 로딩 중 오류 발생: {e}")
        st.stop()

    try:
        df_coords = pd.read_excel('data/coords.xlsx').rename(columns={'행정구역(읍면동)': '읍면동'})
    except FileNotFoundError:
        st.error("'data/coords.xlsx' 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
        st.stop()
    except Exception as e:
        st.error(f"coords.xlsx 데이터 로딩 중 오류 발생: {e}")
        st.stop()

    return df_weather, df_citrus, df_coords

df_weather, df_citrus, df_coords = load_data()

# --- 전처리 ---
df_weather['일시'] = pd.to_datetime(df_weather['일시'])
df_weather['월'] = df_weather['일시'].dt.month
df_weather['연도'] = df_weather['일시'].dt.year

# 감귤 총재배량
prod_cols = ['노지온주(극조생)', '노지온주(조생)', '노지온주(보통)', '하우스감귤(조기출하)',
             '비가림(월동)감귤', '만감류(시설)', '만감류(노지)']
existing_prod_cols = [col for col in prod_cols if col in df_citrus.columns]
if not existing_prod_cols:
    st.warning("총재배량 계산에 필요한 컬럼이 df_citrus에 없습니다.")
    df_citrus['총재배량(톤)'] = 0
else:
    df_citrus['총재배량(톤)'] = df_citrus[existing_prod_cols].sum(axis=1, numeric_only=True)

df_coords['읍면동'] = df_coords['읍면동'].str.strip()
df_citrus['읍면동'] = df_citrus['읍면동'].str.strip()


# --- 관측소 좌표 (실제 정확한 좌표로 대체 권장) ---
observatory_locations = {
    '제주시': (33.51411, 126.52919),   # 제주지방기상청
    '고산': (33.29382, 126.16283),     # 고산기상레이더관측소 (또는 고산 자동기상관측소)
    '성산': (33.46483, 126.91336),     # 성산 자동기상관측소
    '서귀포시': (33.24616, 126.56530)  # 서귀포 자동기상관측소
}
df_observatory_coords = pd.DataFrame.from_dict(observatory_locations, orient='index', columns=['관측소_위도', '관측소_경도']).reset_index().rename(columns={'index': '지점명'})

# --- 읍면동 → 최근접 관측소 동적 매핑 ---
def find_nearest_observatory(lat, lon, observatories_df):
    if pd.isna(lat) or pd.isna(lon):
        return '제주시' # 기본값 (좌표 없는 읍면동의 경우)
    
    min_dist = float('inf')
    nearest_observatory = '제주시' # 기본값

    for _, obs_row in observatories_df.iterrows():
        try:
            dist = geodesic((lat, lon), (obs_row['관측소_위도'], obs_row['관측소_경도'])).km
            if dist < min_dist:
                min_dist = dist
                nearest_observatory = obs_row['지점명']
        except ValueError: # 유효하지 않은 좌표 값의 경우
            continue 
            
    return nearest_observatory

if '위도' in df_coords.columns and '경도' in df_coords.columns:
    df_coords['지점명'] = df_coords.apply(
        lambda row: find_nearest_observatory(row['위도'], row['경도'], df_observatory_coords),
        axis=1
    )
else:
    st.error("df_coords에 '위도' 또는 '경도' 컬럼이 없습니다. 최근접 관측소 매핑을 수행할 수 없습니다.")
    # 모든 읍면동에 기본 '지점명' 할당 또는 앱 중단
    df_coords['지점명'] = '제주시' # 임시방편
    # st.stop()

# --- 연도 선택 ---
if '연도' not in df_citrus.columns:
    st.error("df_citrus에 '연도' 컬럼이 없습니다.")
    st.stop()
available_years_series = df_citrus['연도'].dropna().unique()
try:
    available_years = sorted([int(year) for year in available_years_series], reverse=True)
except ValueError:
    available_years = sorted(list(available_years_series), reverse=True)

if not available_years:
    st.warning("선택 가능한 연도가 없습니다.")
    st.stop()
selected_year = st.selectbox("확인할 연도를 선택하세요", available_years, index=0 if available_years else -1)


# --- 기상 데이터 집계 (선택된 연도 기준) ---
df_weather_year = df_weather[df_weather['연도'] == selected_year]
if df_weather_year.empty:
    st.warning(f"{selected_year}년의 기상 데이터가 없습니다. 다른 연도를 선택해주세요.")
    # 빈 DataFrame을 생성하여 이후 merge에서 오류가 발생하지 않도록 함
    df_weather_agg = pd.DataFrame(columns=['지점명', '평균기온(°C)', '평균상대습도(%)', '월합강수량(00~24h만)(mm)', '평균풍속(m/s)', '합계 일조시간(hr)'])
else:
    df_weather_agg = df_weather_year.groupby('지점명').agg(
        평균기온_C=('평균기온(°C)', 'mean'),
        평균상대습도_perc=('평균상대습도(%)', 'mean'),
        연간총강수량_mm=('월합강수량(00~24h만)(mm)', 'sum'), # 연간 총 강수량
        평균풍속_ms=('평균풍속(m/s)', 'mean'),
        연간총일조시간_hr=('합계 일조시간(hr)', 'sum')      # 연간 총 일조시간
    ).reset_index()
    # 컬럼명 원복 또는 새로운 의미있는 이름 사용
    df_weather_agg = df_weather_agg.rename(columns={
        '평균기온_C': '평균기온(°C)',
        '평균상대습도_perc': '평균상대습도(%)',
        '연간총강수량_mm': '연간총강수량(mm)',
        '평균풍속_ms': '평균풍속(m/s)',
        '연간총일조시간_hr': '연간총일조시간(hr)'
    })

# --- 병합 ---
df_citrus_selected_year = df_citrus[df_citrus['연도'] == selected_year]
df_base = df_coords.merge(df_citrus_selected_year, on='읍면동', how='left')
df_final = df_base.merge(df_weather_agg, on='지점명', how='left') # 최종 데이터프레임 이름을 df_final로 변경


# --- 적합도 계산 (연간 기준) ---
# 중요: 아래 기준값은 예시이며, 실제 감귤 품종 및 재배 환경에 맞게 전문가의 검토를 거쳐 수정해야 합니다.

# 평균기온: 연평균 15~20°C (너무 덥거나 추운 곳은 부적합)
df_final['기온적합'] = df_final['평균기온(°C)'].apply(lambda x: 1 if pd.notnull(x) and 15 <= x <= 20 else 0)
# 평균상대습도: 연평균 60~80%
df_final['습도적합'] = df_final['평균상대습도(%)'].apply(lambda x: 1 if pd.notnull(x) and 60 <= x <= 80 else 0)
# 연간총강수량: 800mm ~ 2000mm (너무 적거나 많으면 문제)
df_final['강수적합'] = df_final['연간총강수량(mm)'].apply(lambda x: 1 if pd.notnull(x) and 800 <= x <= 2000 else 0)
# 평균풍속: 3.0 m/s 이하 (너무 강한 바람은 수정, 낙과 등 피해)
df_final['풍속적합'] = df_final['평균풍속(m/s)'].apply(lambda x: 1 if pd.notnull(x) and x <= 3.0 else 0)
# 연간총일조시간: 1800시간 이상 (충분한 일조량은 당도 향상)
df_final['일조적합'] = df_final['연간총일조시간(hr)'].apply(lambda x: 1 if pd.notnull(x) and x >= 1800 else 0)

df_final['적합도점수'] = df_final[['기온적합', '습도적합', '강수적합', '풍속적합', '일조적합']].sum(axis=1)
df_final['결과'] = df_final['적합도점수'].apply(lambda x: '적합' if x >= 4 else ('보통' if x == 3 else '부적합'))

# --- 지도 시각화 ---
st.subheader(f"🗺️ {selected_year}년 기준 감귤 재배량 및 적합도 지도")

if df_final.empty or '위도' not in df_final.columns or '경도' not in df_final.columns:
    st.warning("지도에 표시할 데이터가 없습니다.")
else:
    m = folium.Map(location=[33.37, 126.53], zoom_start=9) # 제주도 중심 및 줌 레벨

    for _, row in df_final.iterrows():
        if pd.notnull(row['위도']) and pd.notnull(row['경도']):
            color = 'green' if row['결과'] == '적합' else ('orange' if row['결과'] == '보통' else 'red')
            
            total_production = row.get('총재배량(톤)')
            total_production_display = f"{total_production:.1f}톤" if pd.notnull(total_production) else "정보 없음"
            
            avg_temp = row.get('평균기온(°C)')
            avg_temp_display = f"{avg_temp:.1f}°C" if pd.notnull(avg_temp) else "N/A"

            popup_html = f"""
            <b>{row['읍면동']} ({row['결과']})</b><br>
            --------------------<br>
            총재배량: {total_production_display}<br>
            평균기온: {avg_temp_display}<br>
            적합도점수: {int(row['적합도점수'])}/5<br>
            가까운 관측소: {row['지점명']}
            """
            folium.CircleMarker(
                location=[row['위도'], row['경도']],
                radius=max(5, min(row.get('총재배량(톤)', 0) / 2000, 12)) if pd.notnull(row.get('총재배량(톤)')) else 6, # 재배량에 따라 원 크기 (값 조정으로 크기 변경)
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                tooltip=f"{row['읍면동']} - {row['결과']}",
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(m)

    st_folium(m, width=1000, height=600)

# --- 요약 테이블 ---
st.subheader("📋 지역별 요약 정보")
display_cols = ['읍면동', '결과', '적합도점수', '총재배량(톤)', '평균기온(°C)', '평균상대습도(%)', '연간총강수량(mm)', '평균풍속(m/s)', '연간총일조시간(hr)', '지점명']
existing_display_cols = [col for col in display_cols if col in df_final.columns]

df_summary = df_final[df_final['결과'].isin(['적합', '보통'])][existing_display_cols]
if not df_summary.empty:
    st.dataframe(df_summary.sort_values(by='적합도점수', ascending=False).reset_index(drop=True))
else:
    st.write("적합 또는 보통으로 평가된 지역이 없습니다.")

st.markdown("""
---
**참고 사항:**
- **최근접 관측소 매핑:** 각 읍면동의 좌표를 기준으로 가장 가까운 주요 기상 관측소(제주시, 고산, 성산, 서귀포시)의 데이터를 사용합니다. 관측소의 좌표는 예시이며, 더 정확한 좌표 사용 시 결과가 달라질 수 있습니다.
- **적합도 기준:** 제시된 기온, 습도, 강수량, 풍속, 일조시간 기준은 **일반적인 예시**이며, 실제 감귤 품종, 대목, 재배 기술 및 목표 품질에 따라 달라질 수 있습니다. **반드시 전문가의 자문을 받아 해당 지역 및 품종에 맞는 기준으로 조정**해야 합니다.
  - '연간총강수량(mm)' 및 '연간총일조시간(hr)'은 선택된 연도의 **연간 총합계**를 의미합니다.
- **데이터 출처:** ASOS 기상자료 (가공), 농산물 생산량 통계 (가상), 읍면동 좌표 (가상). 실제 데이터 사용 시 결과의 정확도가 향상됩니다.
""")
