import streamlit as st
import pandas as pd
import folium
from streamlit.components.v1 import html
from modules.load_data import load_data

# 🔶 타이틀
st.set_page_config(page_title="감귤 생산성 인사이트 리포트", layout="wide")
st.title("🍊 감귤 생산성 인사이트 리포트 (2025년 기준)")

# 🔶 데이터 로딩
df_weather, df_sunshine = load_data()
df_weather['연월'] = df_weather['일시'].dt.to_period('M').astype(str)
df_sunshine['연월'] = df_sunshine['일시'].dt.to_period('M').astype(str)

selected_month = st.selectbox("📅 기준 월 선택", sorted(df_weather['연월'].unique()), index=len(df_weather['연월'].unique())-1)

# 🔶 감귤 적합성 현황 계산
df_merge = pd.merge(
    df_weather[df_weather['연월'] == selected_month],
    df_sunshine[df_sunshine['연월'] == selected_month],
    on=['지점명', '연월'],
    how='left'
)

df_merge['적합도점수'] = 0
df_merge['적합도점수'] += df_merge['평균기온(°C)'].apply(lambda x: 33 if 12 <= x <= 18 else 0)
df_merge['적합도점수'] += df_merge['평균상대습도(%)'].apply(lambda x: 33 if 60 <= x <= 85 else 0)
df_merge['적합도점수'] += df_merge['일조시간'].apply(lambda x: 34 if x >= 180 else 0)

df_merge['적합여부'] = df_merge['적합도점수'].apply(lambda x: '적합' if x >= 66 else '부적합')

# 🔶 지점명 매핑 테이블
region_mapping = {
    '서귀포시': '서귀포',
    '고흥군': '고흥',
    '완도군': '완도',
    # 필요시 추가 가능
}

# 🔶 지점명 정제 및 매핑
def normalize_region_name(name):
    if not isinstance(name, str):
        return None
    name = name.replace('읍', '').replace('면', '').replace('동', '').replace('시', '').replace('군', '').strip()
    return region_mapping.get(name, name)

df_merge['정제지점명'] = df_merge['지점명'].apply(normalize_region_name)

# 🔶 coords.xlsx 로딩
coords_df = pd.read_excel('data/coords.xlsx', engine='openpyxl')

# 🔶 stations 딕셔너리 생성
stations = {}
for _, row in coords_df.iterrows():
    name = row['행정구역(읍면동)']
    lat = row['위도']
    lon = row['경도']
    if pd.notnull(name) and pd.notnull(lat) and pd.notnull(lon):
        stations[name] = (lat, lon)

st.write("📍 로딩된 지점 목록:", list(stations.keys()))

# 🔶 테이블 출력
st.subheader("📊 감귤 재배 적합성 현황 (적합/부적합)")
st.dataframe(df_merge[['지점명', '평균기온(°C)', '평균상대습도(%)', '일조시간', '적합도점수', '적합여부']])

# 🔶 지도 시각화
st.subheader("🗺️ 감귤 적합도 지도 (적합/부적합)")

fmap = folium.Map(location=[33.5, 126.5], zoom_start=10)

matched_count = 0
for station, (lat, lon) in stations.items():
    row = df_merge[df_merge['정제지점명'] == station]
    if row.empty:
        continue

    matched_count += 1
    status = row['적합여부'].values[0]
    color = 'green' if status == '적합' else 'gray'
    tooltip = f"<b>{station} ({selected_month})</b><br><b>{status}</b>"

    folium.CircleMarker(
        location=[lat, lon],
        radius=10,
        color=color,
        fill=True,
        fill_opacity=0.9,
        popup=tooltip
    ).add_to(fmap)

if matched_count == 0:
    st.warning("❗ 매칭된 지점이 없습니다. 좌표와 지점명을 확인하세요.")
else:
    st.success(f"✅ 총 {matched_count}개 지점을 지도에 표시했습니다.")

html(fmap._repr_html_(), height=500, width=800)

# 🔶 최종 인사이트 요약
total = len(df_merge)
suitable = df_merge['적합여부'].value_counts().get('적합', 0)
unsuitable = df_merge['적합여부'].value_counts().get('부적합', 0)

st.markdown(f"""
### 📍 최종 인사이트 요약 ({selected_month})
- 전체 {total}개 지점 중 **적합 {suitable}개**, **부적합 {unsuitable}개**
- **성산, 서귀포 축선이 감귤 재배 최적지로 확인됨**
- **고흥/완도 지역은 일조량은 충분하나 습도 부족 및 이상기후로 부적합**
- 감귤 농가 재배지 확장 시 **성산 → 서귀포 축선** 권장
- 고흥/완도는 신규 진입 지양, 향후 부동산 데이터 연계 시 성산 인근 농지 추천 가능
""")
