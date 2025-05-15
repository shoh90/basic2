import streamlit as st
import pandas as pd
import sqlite3 # SQLite 모듈 임포트
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 🔶 타이틀
st.set_page_config(page_title="감귤 생산성 인사이트 리포트", layout="wide")
st.title("🍊 감귤 생산성 인사이트 리포트 (2025년 기준)")

# --- 데이터 로딩 및 전처리 함수 (DB에서 로드) ---
@st.cache_data
def load_data_from_db(db_path='asos_weather.db'):
    df_pest_4_db = pd.DataFrame()
    df_pest_5_pivot_db = pd.DataFrame()
    df_weather_asos_db = pd.DataFrame()

    try:
        conn = sqlite3.connect(db_path)

        # 1. pest_disease_4 테이블 로드
        try:
            query_pest_4 = "SELECT * FROM pest_disease_4"
            df_pest_4_db = pd.read_sql_query(query_pest_4, conn)
            if not df_pest_4_db.empty:
                # 컬럼명에 BOM 문자가 있을 경우를 대비 (DB 저장 시 보통 제거됨)
                if '\ufeff연도' in df_pest_4_db.columns:
                    df_pest_4_db.rename(columns={'\ufeff연도':'연도'}, inplace=True)
                df_pest_4_db.rename(columns={'행정구역(읍면동)': '읍면동',
                                              '재배면적(ha)': '면적',
                                              '재배량(톤)': '생산량'}, inplace=True, errors='ignore')
                df_pest_4_db = df_pest_4_db[['연도', '읍면동', '면적', '생산량']]
                df_pest_4_db[['면적', '생산량']] = df_pest_4_db[['면적', '생산량']].apply(pd.to_numeric, errors='coerce').fillna(0)
        except Exception as e:
            st.warning(f"pest_disease_4 테이블 로드 중 오류: {e}")


        # 2. pest_disease_5 테이블 로드 및 pivot
        try:
            query_pest_5 = "SELECT * FROM pest_disease_5"
            df_pest_5_db = pd.read_sql_query(query_pest_5, conn)
            if not df_pest_5_db.empty:
                # 컬럼 이름에서 공백 및 특수문자 제거 (있을 경우)
                df_pest_5_db.columns = df_pest_5_db.columns.str.replace('\ufeff', '').str.strip()
                df_pest_5_db.rename(columns={'연도':'연도', '읍면동':'읍면동', '구분':'구분'}, inplace=True, errors='ignore')

                value_vars = [col for col in df_pest_5_db.columns if col not in ['연도', '읍면동', '구분', '데이터기준일']]
                df_pest_5_melted = df_pest_5_db.melt(
                    id_vars=['연도', '읍면동', '구분'],
                    value_vars=value_vars,
                    var_name='감귤품종',
                    value_name='값'
                )
                df_pest_5_melted['값'] = pd.to_numeric(df_pest_5_melted['값'], errors='coerce').fillna(0)
                df_pest_5_pivot_db = df_pest_5_melted.pivot_table(
                    index=['연도', '읍면동', '감귤품종'],
                    columns='구분',
                    values='값',
                    aggfunc='sum'
                ).reset_index()
                df_pest_5_pivot_db.columns.name = None
                df_pest_5_pivot_db.rename(columns={'면적': '면적', '생산량': '생산량', '농가수': '농가수'}, inplace=True, errors='ignore')
        except Exception as e:
            st.warning(f"pest_disease_5 테이블 로드 중 오류: {e}")


        # 3. asos_weather 테이블 로드
        try:
            query_weather = "SELECT * FROM asos_weather"
            df_weather_asos_db = pd.read_sql_query(query_weather, conn)
            if not df_weather_asos_db.empty:
                if '\ufeff지점' in df_weather_asos_db.columns:
                     df_weather_asos_db.rename(columns={'\ufeff지점':'지점'}, inplace=True)
                
                try:
                    # 'YYYY-MM' 형식이므로, 일(day)을 추가하여 datetime으로 변환
                    df_weather_asos_db['일시'] = pd.to_datetime(df_weather_asos_db['일시'] + '-01')
                except Exception as e_dt:
                     # 만약 '일시' 컬럼 형식이 'YYYY-MM-DD'라면 아래 코드를 사용
                     # df_weather_asos_db['일시'] = pd.to_datetime(df_weather_asos_db['일시'])
                    st.warning(f"asos_weather '일시' 컬럼을 datetime으로 변환 중 오류: {e_dt}. 수동 확인 필요.")

                df_weather_asos_db['연월'] = df_weather_asos_db['일시'].dt.to_period('M').astype(str)
        except Exception as e:
            st.warning(f"asos_weather 테이블 로드 중 오류: {e}")

        conn.close()
        return df_pest_4_db, df_pest_5_pivot_db, df_weather_asos_db

    except sqlite3.Error as e:
        st.error(f"SQLite 데이터베이스 연결 오류: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"전체 데이터 로딩 중 오류 발생: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로딩
df_prod_jejusi, df_prod_seogwipo_pivot, df_weather_asos = load_data_from_db()

# --- 1. 제주 감귤 농산물 현황 ---
st.header("1. 제주 감귤 농산물 현황")

# 1.1 데이터 집계 (연도별 총계)
# ... (이전과 동일한 집계 로직, 단, df_prod_jejusi, df_prod_seogwipo_pivot, df_weather_asos는 위에서 로드된 DB 기반 데이터 사용)

# 서귀포시 데이터에서 연도별 총계 계산
if not df_prod_seogwipo_pivot.empty:
    df_seogwipo_yearly_sum = df_prod_seogwipo_pivot.groupby('연도').agg(
        면적_서귀포=('면적', 'sum'),
        생산량_서귀포=('생산량', 'sum'),
        농가수_서귀포=('농가수', 'sum')
    ).reset_index()
else:
    df_seogwipo_yearly_sum = pd.DataFrame(columns=['연도', '면적_서귀포', '생산량_서귀포', '농가수_서귀포'])


# 제주시 데이터에서 연도별 총계 계산
if not df_prod_jejusi.empty:
    df_jejusi_yearly_sum = df_prod_jejusi.groupby('연도').agg(
        면적_제주시=('면적', 'sum'),
        생산량_제주시=('생산량', 'sum')
    ).reset_index()
else:
    df_jejusi_yearly_sum = pd.DataFrame(columns=['연도', '면적_제주시', '생산량_제주시'])

# 연도별 총 생산 현황 데이터프레임 생성
if not df_jejusi_yearly_sum.empty and not df_seogwipo_yearly_sum.empty:
    df_total_yearly = pd.merge(df_jejusi_yearly_sum, df_seogwipo_yearly_sum, on='연도', how='outer').fillna(0)
    df_total_yearly['총재배면적(ha)'] = df_total_yearly['면적_제주시'] + df_total_yearly['면적_서귀포']
    df_total_yearly['총생산량(천톤)'] = (df_total_yearly['생산량_제주시'] + df_total_yearly['생산량_서귀포']) / 1000
    df_total_yearly['총농가수(호)'] = df_total_yearly['농가수_서귀포'] # 개선 필요
    df_total_yearly = df_total_yearly[['연도', '총재배면적(ha)', '총생산량(천톤)', '총농가수(호)']].sort_values(by='연도')
elif not df_seogwipo_yearly_sum.empty:
    df_total_yearly = df_seogwipo_yearly_sum.rename(columns={
        '면적_서귀포':'총재배면적(ha)', '생산량_서귀포':'총생산량(천톤)', '농가수_서귀포':'총농가수(호)'
    })
    df_total_yearly['총생산량(천톤)'] = df_total_yearly['총생산량(천톤)'] / 1000
    df_total_yearly = df_total_yearly[['연도', '총재배면적(ha)', '총생산량(천톤)', '총농가수(호)']].sort_values(by='연도')
elif not df_prod_jejusi.empty: # df_jejusi_yearly_sum 대신 df_prod_jejusi 로 조건 수정
    df_total_yearly = df_jejusi_yearly_sum.rename(columns={
        '면적_제주시':'총재배면적(ha)', '생산량_제주시':'총생산량(천톤)'
    })
    df_total_yearly['총생산량(천톤)'] = df_total_yearly['총생산량(천톤)'] / 1000
    df_total_yearly['총농가수(호)'] = 0
    df_total_yearly = df_total_yearly[['연도', '총재배면적(ha)', '총생산량(천톤)', '총농가수(호)']].sort_values(by='연도')
else:
    df_total_yearly = pd.DataFrame(columns=['연도', '총재배면적(ha)', '총생산량(천톤)', '총농가수(호)'])

df_total_yearly['조수입(억원)'] = 0 # 더미값

# 1.2 KPI 카드
# ... (이전과 동일) ...
if not df_total_yearly.empty:
    latest_year_data = df_total_yearly.iloc[-1]
    previous_year_data = df_total_yearly.iloc[-2] if len(df_total_yearly) > 1 else latest_year_data

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
        delta=f"{latest_year_data['총농가수(호)'] - previous_year_data['총농가수(호)']:.1f} 호 (전년 대비)" if latest_year_data['총농가수(호)'] > 0 and previous_year_data['총농가수(호)'] > 0 else "N/A",
        delta_color="normal" if latest_year_data['총농가수(호)'] > previous_year_data['총농가수(호)'] else "inverse"
    )
    col4.metric(label=f"{latest_year_data['연도']}년 조수입", value="데이터 없음", delta="N/A")
else:
    st.warning("생산량 데이터를 불러오지 못했거나 데이터가 비어있습니다.")

# 1.3 혼합 차트
# ... (이전과 동일) ...
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
    fig.update_layout(
        title_text="<b>연도별 감귤 생산 현황</b>",
        xaxis_title="연도",
        legend_title_text="지표"
    )
    fig.update_yaxes(title_text="<b>생산량 (천톤)</b>", secondary_y=False)
    fig.update_yaxes(title_text="<b>재배면적 (ha)</b>", secondary_y=True) # 조수입 제외
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("연도별 상세 데이터")
    # NaN 값을 0으로 채우고 정수형으로 표시할 컬럼 지정
    format_dict = {'총재배면적(ha)': "{:.0f}", '총농가수(호)': "{:.0f}", '총생산량(천톤)': "{:.1f}"}
    # '연도'를 object (문자열) 타입으로 변경하여 소수점 표시 방지
    df_display = df_total_yearly.astype({'연도': str}).copy()
    st.dataframe(df_display.set_index('연도').style.format(format_dict))


    st.info("""
    **주요 분석:** (샘플 분석입니다. 실제 데이터에 맞게 수정하세요.)
    *   생산량 및 재배면적 추세를 확인하여 감귤 산업의 전반적인 규모 변화를 파악합니다.
    *   농가수 변화를 통해 산업 참여 구조의 변화를 유추할 수 있습니다.
    """)
else:
    st.info("생산 현황 차트 및 테이블을 표시할 데이터가 없습니다.")


st.markdown("---")

# --- 기상 데이터 현황 (DB 기반) ---
st.header("기상 데이터 현황 (asos_weather.db 기반)")
if not df_weather_asos.empty:
    st.subheader("ASOS 기상 데이터 샘플 (DB에서 로드)")
    st.dataframe(df_weather_asos.head())

    # 예시: 특정 지점의 월별 평균 기온 변화
    if '지점명' in df_weather_asos.columns and '평균기온(°C)' in df_weather_asos.columns:
        available_stations = df_weather_asos['지점명'].unique()
        if len(available_stations) > 0:
            selected_station_weather = st.selectbox("기상 관측 지점 선택", available_stations)
            df_station_weather = df_weather_asos[df_weather_asos['지점명'] == selected_station_weather]
            if not df_station_weather.empty:
                fig_temp_station = px.line(df_station_weather, x='일시', y='평균기온(°C)', title=f'{selected_station_weather} 월별 평균 기온 변화')
                st.plotly_chart(fig_temp_station, use_container_width=True)
            else:
                st.warning(f"{selected_station_weather} 지역 기상 데이터가 없습니다.")
        else:
            st.warning("기상 데이터에 유효한 지점 정보가 없습니다.")
    else:
        st.warning("기상 데이터에 '지점명' 또는 '평균기온(°C)' 컬럼이 없습니다.")
else:
    st.warning("ASOS 기상 데이터를 데이터베이스에서 불러오지 못했습니다.")
