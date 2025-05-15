import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 🔶 타이틀
st.set_page_config(page_title="감귤 생산성 인사이트 리포트", layout="wide")
st.title("🍊 감귤 생산성 인사이트 리포트 (2025년 기준)")

# --- 데이터 로딩 및 전처리 함수 ---
@st.cache_data
def load_production_data():
    # pest_disease_4.csv 로드 (제주시 중심 데이터로 가정)
    try:
        df_pest_4 = pd.read_csv('pest_disease_4.csv', encoding='utf-8-sig')
        df_pest_4.rename(columns={'행정구역(읍면동)': '읍면동',
                                  '재배면적(ha)': '면적',
                                  '재배량(톤)': '생산량',
                                  '\ufeff연도':'연도'}, inplace=True) # BOM 문자 처리
        # 필요한 컬럼만 선택하고, 숫자형으로 변환 (오류 발생 시 0으로)
        df_pest_4 = df_pest_4[['연도', '읍면동', '면적', '생산량']]
        df_pest_4[['면적', '생산량']] = df_pest_4[['면적', '생산량']].apply(pd.to_numeric, errors='coerce').fillna(0)
    except FileNotFoundError:
        st.error("pest_disease_4.csv 파일을 찾을 수 없습니다.")
        return pd.DataFrame(), pd.DataFrame() # 빈 데이터프레임 반환

    # pest_disease_5.csv 로드 및 pivot (서귀포시 중심 데이터로 가정)
    try:
        df_pest_5 = pd.read_csv('pest_disease_5.csv', encoding='utf-8-sig')
        # 컬럼 이름에서 공백 및 특수문자 제거 (있을 경우)
        df_pest_5.columns = df_pest_5.columns.str.replace('\ufeff', '').str.strip() # BOM 및 공백 제거
        df_pest_5.rename(columns={'연도':'연도', '읍면동':'읍면동', '구분':'구분'}, inplace=True)

        # 읍면동, 연도, 구분을 제외한 나머지 컬럼은 감귤 종류별 값으로 간주
        value_vars = [col for col in df_pest_5.columns if col not in ['연도', '읍면동', '구분', '데이터기준일']]

        df_pest_5_melted = df_pest_5.melt(
            id_vars=['연도', '읍면동', '구분'],
            value_vars=value_vars,
            var_name='감귤품종',
            value_name='값'
        )
        df_pest_5_melted['값'] = pd.to_numeric(df_pest_5_melted['값'], errors='coerce').fillna(0)

        # '구분' (면적, 생산량, 농가수)을 컬럼으로 pivot
        df_pest_5_pivot = df_pest_5_melted.pivot_table(
            index=['연도', '읍면동', '감귤품종'],
            columns='구분',
            values='값',
            aggfunc='sum' # 혹시 모를 중복에 대비해 sum 사용
        ).reset_index()
        df_pest_5_pivot.columns.name = None # pivot_table로 생긴 columns.name 제거

        # 컬럼명 정리 (예: '면적(ha)', '생산량(톤)')
        df_pest_5_pivot.rename(columns={'면적': '면적', '생산량': '생산량', '농가수': '농가수'}, inplace=True, errors='ignore')

    except FileNotFoundError:
        st.error("pest_disease_5.csv 파일을 찾을 수 없습니다.")
        return df_pest_4, pd.DataFrame() # df_pest_4는 로드 성공했을 수 있으므로 반환

    return df_pest_4, df_pest_5_pivot

@st.cache_data
def load_weather_data():
    try:
        df_weather_asos = pd.read_csv('asos_weather.csv', encoding='utf-8-sig')
        df_weather_asos.rename(columns={'\ufeff지점':'지점'}, inplace=True) # BOM 문자 처리
        df_weather_asos['일시'] = pd.to_datetime(df_weather_asos['일시'])
        df_weather_asos['연월'] = df_weather_asos['일시'].dt.to_period('M').astype(str)
        return df_weather_asos
    except FileNotFoundError:
        st.error("asos_weather.csv 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

# 데이터 로딩
df_prod_jejusi, df_prod_seogwipo_pivot = load_production_data()
df_weather_asos = load_weather_data()

# --- 1. 제주 감귤 농산물 현황 ---
st.header("1. 제주 감귤 농산물 현황")

# 1.1 데이터 집계 (연도별 총계)
# df_prod_jejusi: 연도, 면적, 생산량 (농가수 데이터는 없음)
# df_prod_seogwipo_pivot: 연도, 읍면동, 감귤품종, 면적, 생산량, 농가수

# 서귀포시 데이터에서 연도별 총계 계산
if not df_prod_seogwipo_pivot.empty:
    # 농가수는 읍면동별로 합산 후, 연도별로 다시 합산 (중복 가능성 있으나 일단 진행)
    # 정확한 농가수 집계를 위해서는 읍면동별 unique 농가수를 더해야 하지만, 현재 데이터 구조로는 어려움.
    # 여기서는 연도별 '농가수' 컬럼의 합계를 사용.
    df_seogwipo_yearly_sum = df_prod_seogwipo_pivot.groupby('연도').agg(
        면적_서귀포=('면적', 'sum'),
        생산량_서귀포=('생산량', 'sum'),
        농가수_서귀포=('농가수', 'sum') # 이 부분은 주의, 품종별 농가수가 중복될 수 있음
    ).reset_index()
else:
    df_seogwipo_yearly_sum = pd.DataFrame(columns=['연도', '면적_서귀포', '생산량_서귀포', '농가수_서귀포'])


# 제주시 데이터에서 연도별 총계 계산
if not df_prod_jejusi.empty:
    df_jejusi_yearly_sum = df_prod_jejusi.groupby('연도').agg(
        면적_제주시=('면적', 'sum'),
        생산량_제주시=('생산량', 'sum')
        # 농가수 데이터는 pest_disease_4.csv에 없음
    ).reset_index()
else:
    df_jejusi_yearly_sum = pd.DataFrame(columns=['연도', '면적_제주시', '생산량_제주시'])

# 연도별 총 생산 현황 데이터프레임 생성 (제주시 + 서귀포시)
if not df_jejusi_yearly_sum.empty and not df_seogwipo_yearly_sum.empty:
    df_total_yearly = pd.merge(df_jejusi_yearly_sum, df_seogwipo_yearly_sum, on='연도', how='outer').fillna(0)
    df_total_yearly['총재배면적(ha)'] = df_total_yearly['면적_제주시'] + df_total_yearly['면적_서귀포']
    df_total_yearly['총생산량(천톤)'] = (df_total_yearly['생산량_제주시'] + df_total_yearly['생산량_서귀포']) / 1000 # 천톤 단위
    df_total_yearly['총농가수(호)'] = df_total_yearly['농가수_서귀포'] # 제주시 농가수 데이터 없으므로 서귀포시 농가수만 사용 (개선 필요)
    df_total_yearly = df_total_yearly[['연도', '총재배면적(ha)', '총생산량(천톤)', '총농가수(호)']].sort_values(by='연도')
elif not df_seogwipo_yearly_sum.empty: # 서귀포 데이터만 있는 경우
    df_total_yearly = df_seogwipo_yearly_sum.rename(columns={
        '면적_서귀포':'총재배면적(ha)',
        '생산량_서귀포':'총생산량(천톤)', # 천톤 단위 변환 필요
        '농가수_서귀포':'총농가수(호)'
    })
    df_total_yearly['총생산량(천톤)'] = df_total_yearly['총생산량(천톤)'] / 1000
    df_total_yearly = df_total_yearly[['연도', '총재배면적(ha)', '총생산량(천톤)', '총농가수(호)']].sort_values(by='연도')
elif not df_jejusi_yearly_sum.empty: # 제주시 데이터만 있는 경우
    df_total_yearly = df_jejusi_yearly_sum.rename(columns={
        '면적_제주시':'총재배면적(ha)',
        '생산량_제주시':'총생산량(천톤)' # 천톤 단위 변환 필요
    })
    df_total_yearly['총생산량(천톤)'] = df_total_yearly['총생산량(천톤)'] / 1000
    df_total_yearly['총농가수(호)'] = 0 # 농가수 데이터 없음
    df_total_yearly = df_total_yearly[['연도', '총재배면적(ha)', '총생산량(천톤)', '총농가수(호)']].sort_values(by='연도')
else:
    df_total_yearly = pd.DataFrame(columns=['연도', '총재배면적(ha)', '총생산량(천톤)', '총농가수(호)'])


# 조수입 데이터는 없으므로 더미값 또는 메시지 표시
df_total_yearly['조수입(억원)'] = 0 # 더미값, 실제 데이터로 대체 필요

# 1.2 KPI 카드
if not df_total_yearly.empty:
    latest_year_data = df_total_yearly.iloc[-1]
    previous_year_data = df_total_yearly.iloc[-2] if len(df_total_yearly) > 1 else latest_year_data # 전년도 데이터 없으면 현재년도로

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        label=f"{latest_year_data['연도']}년 생산량",
        value=f"{latest_year_data['총생산량(천톤)']:.0f} 천톤",
        delta=f"{latest_year_data['총생산량(천톤)'] - previous_year_data['총생산량(천톤)']:.1f} 천톤 (전년 대비)",
        delta_color="inverse" if latest_year_data['총생산량(천톤)'] < previous_year_data['총생산량(천톤)'] else "normal"
    )
    col2.metric(
        label=f"{latest_year_data['연도']}년 재배면적",
        value=f"{latest_year_data['총재배면적(ha)']:.0f} ha",
        delta=f"{latest_year_data['총재배면적(ha)'] - previous_year_data['총재배면적(ha)']:.1f} ha (전년 대비)",
        delta_color="inverse" if latest_year_data['총재배면적(ha)'] < previous_year_data['총재배면적(ha)'] else "normal"
    )
    col3.metric(
        label=f"{latest_year_data['연도']}년 농가수",
        value=f"{latest_year_data['총농가수(호)']:.0f} 호",
        delta=f"{latest_year_data['총농가수(호)'] - previous_year_data['총농가수(호)']:.1f} 호 (전년 대비)" if latest_year_data['총농가수(호)'] > 0 else "N/A",
        delta_color="normal" if latest_year_data['총농가수(호)'] > previous_year_data['총농가수(호)'] else "inverse"
    )
    # 조수입 데이터가 없으므로 일단 제외 또는 더미로 표시
    col4.metric(label=f"{latest_year_data['연도']}년 조수입", value="데이터 없음", delta="N/A")
else:
    st.warning("생산량 데이터를 불러오지 못했거나 데이터가 비어있습니다.")

# 1.3 혼합 차트 (생산량, 재배면적, 조수입)
if not df_total_yearly.empty:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=df_total_yearly['연도'], y=df_total_yearly['총생산량(천톤)'], name="생산량(천톤)", mode='lines+markers'),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=df_total_yearly['연도'], y=df_total_yearly['총재배면적(ha)'], name="재배면적(ha)", mode='lines+markers'),
        secondary_y=True,
    )
    # 조수입 데이터가 있다면 추가
    # fig.add_trace(
    #     go.Scatter(x=df_total_yearly['연도'], y=df_total_yearly['조수입(억원)'], name="조수입(억원)", mode='lines+markers'),
    #     secondary_y=True, # 필요에 따라 다른 Y축 사용
    # )

    fig.update_layout(
        title_text="<b>연도별 감귤 생산 현황</b>",
        xaxis_title="연도",
        legend_title_text="지표"
    )
    fig.update_yaxes(title_text="<b>생산량 (천톤)</b>", secondary_y=False)
    fig.update_yaxes(title_text="<b>재배면적 (ha) / 조수입 (억원)</b>", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

    # 1.4 데이터 테이블
    st.subheader("연도별 상세 데이터")
    st.dataframe(df_total_yearly.set_index('연도').style.format("{:.0f}", subset=['총재배면적(ha)', '총농가수(호)']).format("{:.1f}", subset=['총생산량(천톤)']))

    # 1.5 주요 분석
    st.info("""
    **주요 분석:**
    *   생산량은 지속적으로 감소 추세를 보이고 있으나, 조수입은 증가 (조수입 데이터 확보 시 분석 가능)
    *   재배면적 감소에도 불구하고 농가수는 2023년에 증가 - 소규모 농가 증가 추세 (농가수 데이터 정확도 확인 필요)
    *   단위 면적당 생산량은 감소하나 감귤 가격 상승으로 인한 조수입 증가 (가정, 데이터 기반 분석 필요)
    """)
else:
    st.info("생산 현황 차트 및 테이블을 표시할 데이터가 없습니다.")


st.markdown("---") # 구분선

# --- 기상 데이터 로직 수정 (asos_weather.csv 활용) ---
# 이 부분은 다른 탭이나 섹션에서 활용될 것이므로, 일단 df_weather_asos를 로드해두는 것으로 준비.
# 기존 코드에서 df_merged를 만들던 부분을 수정해야 함.

st.header("기상 데이터 현황 (asos_weather.csv 기반)")
if not df_weather_asos.empty:
    st.subheader("ASOS 기상 데이터 샘플")
    st.dataframe(df_weather_asos.head())

    # 예시: 특정 지점의 월별 평균 기온 변화 (다른 탭에서 활용될 수 있음)
    # 제주 지점(184) 데이터 필터링
    df_jeju_weather = df_weather_asos[df_weather_asos['지점명'] == '제주']
    if not df_jeju_weather.empty:
        fig_temp_jeju = px.line(df_jeju_weather, x='일시', y='평균기온(°C)', title='제주 월별 평균 기온 변화')
        st.plotly_chart(fig_temp_jeju, use_container_width=True)
    else:
        st.warning("제주 지역 기상 데이터가 없습니다.")
else:
    st.warning("ASOS 기상 데이터를 불러오지 못했습니다.")

# 여기에 2, 3, 4, 5번 섹션 구현 코드가 이어집니다.
# 우선은 1번 섹션과 기상 데이터 로드 부분만 중점적으로 작성했습니다.
