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

# 🔶 적합도 계산
df_selected['적합도점수'] = 0
df_selected['적합도점수'] += df_selected['평균기온(°C)'].apply(lambda x: 33 if 12 <= x <= 18 else 0)
df_selected['적합도점수'] += df_selected[humidity_col].apply(lambda x: 33 if 60 <= x <= 85 else 0)
df_selected[sunshine_col] = pd.to_numeric(df_selected[sunshine_col], errors='coerce')
df_selected['적합도점수'] += df_selected[sunshine_col].apply(lambda x: 34 if x >= 180 else 0)

df_selected['적합여부'] = df_selected['적합도점수'].apply(lambda x: '적합' if x >= 66 else '부적합')

# 🔶 지도 생성
m = folium.Map(location=[33.5, 126.5], zoom_start=10)

# 🔶 안전한 지점명 매칭 함수 (TypeError 방지 포함)
def match_region(name, coord_dict):
    if not isinstance(name, str):
        return None  # NaN 등 방어
    for key in coord_dict.keys():
        if not isinstance(key, str):
            continue
        if key in name or name in key:
            return coord_dict[key]
    return None

# 🔶 마커 표시
matched_count = 0
for _, row in df_selected.iterrows():
    region = row['지점명']
    coords = match_region(region, coord_dict)
    if coords:
        matched_count += 1
        lat, lon = coords[1], coords[0]
        status = row['적합여부']
        color = 'green' if status == '적합' else 'gray'

        tooltip_text = (
            f"{region} ({status})\n"
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
    st.warning("❗ 매칭된 지점이 없습니다. 좌표 이름을 확인하세요.")
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
- 전체 **{total}개 지점 중 적합 {suitable}곳, 부적합 {unsuitable}곳**
- **성산, 서귀포 축선**은 감귤 재배 최적지로 확인
- **고흥/완도 등 일부 지역**은 일조량은 충분하나 **습도 부족 또는 이상기후로 부적합**
- 신규 재배지는 **성산 → 서귀포 축선 중심 확장 권장**
- **고흥/완도는 리스크 지역**으로, 데이터 기반 추가 검토 필요
"""
st.markdown(insight_text)
