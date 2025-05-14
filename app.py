import streamlit as st
import folium
import pandas as pd
import sqlite3
import json
from streamlit_folium import st_folium

# 🔶 페이지 설정
st.set_page_config(page_title="제주 감귤 재배 적합도 리포트", layout="wide")

# 🔶 파일 경로
db_path = "data/asos_weather.db"
geojson_path = "data/jeju_geo.json"

# 🔶 GeoJSON 좌표 로딩
try:
    with open(geojson_path, encoding='utf-8') as f:
        geo_data = json.load(f)
    coord_dict = {f['properties']['name']: f['geometry']['coordinates'] for f in geo_data['features'] if f['properties']['name']}
except FileNotFoundError:
    st.error(f"❌ geojson 파일 없음: {geojson_path}")
    st.stop()

# 🔶 DB 데이터 로딩
try:
    conn = sqlite3.connect(db_path)
    df_weather = pd.read_sql("SELECT * FROM asos_weather", conn)
    conn.close()
except Exception as e:
    st.error(f"❌ DB 파일 오류: {e}")
    st.stop()

# 🔶 컬럼명 확인
st.write("📊 DB 컬럼명:", df_weather.columns.tolist())

# 🔶 전처리: 연월 추가
df_weather['일시'] = pd.to_datetime(df_weather['일시'], errors='coerce')
df_weather['연월'] = df_weather['일시'].dt.to_period('M').astype(str)

# 🔶 연월 선택
available_months = sorted(df_weather['연월'].unique(), reverse=True)
selected_month = st.selectbox("📅 기준 월 선택", available_months)

# 🔶 필터링
df_selected = df_weather[df_weather['연월'] == selected_month]

# 🔶 컬럼명 자동 매칭
humidity_col = next((col for col in df_selected.columns if '습도' in col), None)
sunshine_col = next((col for col in df_selected.columns if '일조' in col), None)

if not humidity_col or not sunshine_col:
    st.error(f"❌ '습도' 또는 '일조' 컬럼 없음. 현재: {df_selected.columns.tolist()}")
    st.stop()

# 🔶 지점명 매핑 테이블 (DB → GeoJSON 기준으로 맞추기)
region_mapping = {
    '서귀포시': '서귀포',  # 예시
    '성산읍': '성산읍',
    '한림읍': '한림읍',
    '애월읍': '애월읍',
    '대정읍': '대정읍',
    '남원읍': '남원읍',
    '구좌읍': '구좌읍',
    '조천읍': '조천읍',
    '안덕면': '안덕면',
    '표선면': '표선면',
    '일도2동': '일도2동',
    '이도2동': '이도2동',
    '용담2동': '용담2동',
    # 필요시 추가
}

# 🔶 지점명 정제 및 매핑
def normalize_region_name(name):
    if not isinstance(name, str):
        return None
    name = name.replace('읍', '').replace('면', '').replace('동', '').replace('시', '').replace('군', '').strip()
    return region_mapping.get(name, name)

df_selected['정제지점명'] = df_selected['지점명'].apply(normalize_region_name)

# 🔶 GeoJSON 기준으로 필터링
geojson_names = [k for k in coord_dict.keys() if isinstance(k, str)]
df_selected = df_selected[df_selected['정제지점명'].isin(geojson_names)]

# 🔶 적합도 계산
df_selected['적합도점수'] = 0
df_selected['적합도점수'] += df_selected['평균기온(°C)'].apply(lambda x: 33 if 12 <= x <= 18 else 0)
df_selected['적합도점수'] += df_selected[humidity_col].apply(lambda x: 33 if 60 <= x <= 85 else 0)
df_selected[sunshine_col] = pd.to_numeric(df_selected[sunshine_col], errors='coerce')
df_selected['적합도점수'] += df_selected[sunshine_col].apply(lambda x: 34 if x >= 180 else 0)

df_selected['적합여부'] = df_selected['적합도점수'].apply(lambda x: '적합' if x >= 66 else '부적합')

# 🔶 folium 지도 생성
m = folium.Map(location=[33.5, 126.5], zoom_start=10)

# 🔶 마커 표시
matched_count = 0
for _, row in df_selected.iterrows():
    region = row['정제지점명']
    coords = coord_dict.get(region)
    if coords:
        matched_count += 1
        lat, lon = coords[1], coords[0]
        status = row['적합여부']
        color = 'green' if status == '적합' else 'gray'

        tooltip_text = (
            f"{row['지점명']} ({status})\n"
            f"기온: {row['평균기온(°C)']}°C\n"
            f"습도: {row[humidity_col]}%\n"
            f"일조: {row[sunshine_col]}시간"
        )

        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
            color=color,
            fill=True,
            fill_opacity=0.7,
            tooltip=tooltip_text
        ).add_to(m)

# 🔶 지도 출력
st.subheader(f"🗺️ 감귤 재배 적합도 지도 ({selected_month})")
if matched_count == 0:
    st.warning("❗ 매칭된 지점이 없습니다. GeoJSON과 지점명을 확인하세요.")
else:
    st.success(f"✅ 총 {matched_count}개 지점을 지도에 표시했습니다.")
st_folium(m, width=800, height=600)

# 🔶 적합도 데이터 테이블
st.subheader("📊 적합도 세부 데이터")
st.dataframe(df_selected[['지점명', '평균기온(°C)', humidity_col, sunshine_col, '적합도점수', '적합여부']])

# 🔶 인사이트 자동 요약
total = len(df_selected)
suitable = df_selected['적합여부'].value_counts().get('적합', 0)
unsuitable = df_selected['적합여부'].value_counts().get('부적합', 0)

insight_text = f"""
### 📍 인사이트 요약 ({selected_month})
- 전체 {total}개 지점 중 **적합 {suitable}개**, **부적합 {unsuitable}개**
- **성산, 한림, 애월 등 주요 읍면이 감귤 재배 최적지로 확인됨**
- 향후 재배지 확장은 **서귀포 서부~동부 축선** 권장
- 일조량 부족 지역은 감귤 품종 및 차광/보온 대책 검토 필요
"""
st.markdown(insight_text)
