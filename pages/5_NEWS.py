import streamlit as st
import requests
from datetime import datetime
import html

# --- 페이지 설정 ---
st.set_page_config(page_title="🍊 감귤 스마트 뉴스 대시보드", page_icon="🍊", layout="wide")

# --- API 키 로드 ---
try:
    client_id = st.secrets["NAVER_CLIENT_ID"]
    client_secret = st.secrets["NAVER_CLIENT_SECRET"]
except KeyError:
    st.error("Streamlit Secrets에 NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 설정되지 않았습니다.")
    st.error("애플리케이션을 사용하려면 .streamlit/secrets.toml 파일에 API 키를 설정하거나, Streamlit Cloud 환경 변수를 설정해주세요.")
    st.caption("예시: .streamlit/secrets.toml")
    st.code("""
NAVER_CLIENT_ID = "YOUR_CLIENT_ID"
NAVER_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
    """)
    st.stop()


# --- 유틸리티 함수 ---
@st.cache_data(ttl=3600) # 1시간 동안 API 응답 캐싱
def get_naver_news_api(query, display=10, start=1, sort="date"):
    """네이버 뉴스 API를 호출하여 뉴스 아이템 리스트를 반환합니다."""
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    params = {"query": query, "display": display, "start": start, "sort": sort}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10) # 타임아웃 10초
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류 발생: {e}")
        return [] # 오류 발생 시 빈 리스트 반환
    except ValueError as e: # JSON 디코딩 오류
        st.error(f"API 응답 분석 중 오류 발생: {e}")
        return []


def remove_html_tags(text):
    """HTML 태그를 제거하고 엔티티를 변환합니다."""
    return html.unescape(text).replace("<b>", "").replace("</b>", "")

def format_pubdate(pubdate_str):
    """API에서 받은 날짜 문자열을 'YYYY년 MM월 DD일 HH:MM' 형식으로 변환합니다."""
    try:
        dt_obj = datetime.strptime(pubdate_str, '%a, %d %b %Y %H:%M:%S %z')
        return dt_obj.strftime('%Y년 %m월 %d일 %H:%M')
    except ValueError:
        return pubdate_str # 파싱 실패 시 원본 반환

# --- 세션 상태 초기화 ---
if 'query_input' not in st.session_state:
    st.session_state.query_input = "제주 감귤" # 기본 검색어
if 'news_items' not in st.session_state:
    st.session_state.news_items = []
if 'last_searched_query' not in st.session_state: # 실제 검색이 수행된 쿼리
    st.session_state.last_searched_query = ""

# --- 검색 수행 함수 ---
def perform_search(search_query):
    """주어진 검색어로 뉴스를 검색하고 결과를 세션 상태에 저장합니다."""
    if not search_query.strip():
        st.warning("검색어를 입력해주세요.")
        st.session_state.news_items = []
        st.session_state.last_searched_query = ""
        return

    st.session_state.last_searched_query = search_query # 검색 수행한 쿼리 기록
    with st.spinner(f"'{search_query}' 관련 뉴스를 가져오는 중... 잠시만 기다려주세요."):
        news_items_fetched = get_naver_news_api(search_query, display=20) # 최대 20개
        st.session_state.news_items = news_items_fetched

        if not news_items_fetched:
            st.info(f"'{search_query}' 관련 뉴스가 없습니다. 다른 검색어를 시도해보세요.")
        else:
            # 검색 성공 메시지는 뉴스 목록 위에 한 번만 표시되도록 조정 가능
            # 여기서는 검색 버튼 누를 때마다 새로고침되므로 이 위치도 괜찮음
            pass # 성공 메시지는 결과 표시 부분에서 처리할 수 있음

# --- UI 구성 ---
st.title("🍊 실시간 감귤 뉴스 대시보드")
st.markdown("> 네이버 뉴스 API를 활용하여 감귤 및 농업 관련 최신 뉴스를 제공합니다.")
st.markdown("---")

# 추천 키워드
st.markdown("#### ✨ 추천 키워드로 빠르게 검색해보세요!")
recommended_keywords = ["제주 감귤", "감귤 농사", "만감류", "감귤 병해충", "농산물 가격"]
cols = st.columns(len(recommended_keywords))
for i, keyword in enumerate(recommended_keywords):
    if cols[i].button(keyword, key=f"rec_btn_{keyword.replace(' ', '_')}", use_container_width=True):
        st.session_state.query_input = keyword # 텍스트 입력창에도 반영
        perform_search(keyword) # 즉시 검색 실행

st.markdown("<br>", unsafe_allow_html=True) # 추천 키워드와 검색창 사이 간격

# 검색 입력창 및 버튼
search_col1, search_col2 = st.columns([4,1])
with search_col1:
    query_from_input = st.text_input(
        "🔍 검색하고 싶은 키워드를 입력하세요:",
        value=st.session_state.query_input,
        key="main_query_text_input",
        on_change=lambda: setattr(st.session_state, 'query_input', st.session_state.main_query_text_input) # 입력창 변경 시 세션 상태 업데이트
    )
with search_col2:
    st.write("") # 버튼 정렬을 위한 더미 공간
    if st.button("📰 뉴스 검색", use_container_width=True, type="primary"):
        perform_search(st.session_state.query_input)

st.markdown("---")

# 뉴스 결과 표시
if st.session_state.last_searched_query: # 검색이 한 번이라도 수행되었다면
    if st.session_state.news_items:
        st.success(f"'{st.session_state.last_searched_query}' 뉴스 검색 결과 ({len(st.session_state.news_items)}개)")
        for i, news in enumerate(st.session_state.news_items):
            title = remove_html_tags(news['title'])
            description = remove_html_tags(news['description'])
            pub_date = format_pubdate(news['pubDate'])
            main_link = news.get('originallink') if news.get('originallink') else news.get('link')
            naver_news_link = news.get('link')

            with st.container(border=True):
                st.markdown(f"### {i+1}. {title}")
                st.caption(f"🗓️ 게시일: {pub_date}")

                if description:
                    st.markdown(f"> {description}") # 인용구 스타일로 요약 표시

                # 링크 표시 (HTML 사용으로 새 탭에서 열기)
                link_html = f'<a href="{main_link}" target="_blank" style="text-decoration: none; font-weight: bold; color: #FF7F0E;">🔗 기사 원문 읽기</a>'
                if news.get('originallink') and naver_news_link and news['originallink'] != naver_news_link:
                    link_html += f'  <small>(<a href="{naver_news_link}" target="_blank" style="text-decoration: none; color: #1E90FF;">네이버 뉴스에서 보기</a>)</small>'
                st.markdown(link_html, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True) # 각 카드 사이 간격 추가

    # '결과 없음' 메시지는 perform_search에서 이미 처리되었으므로, 여기서는 특별히 추가할 필요 없음
    # (perform_search 내 st.info가 호출됨)

elif not st.session_state.news_items and not st.session_state.last_searched_query : # 앱 처음 실행 시 또는 검색 전
    st.info("💁‍♀️ 상단에서 검색어를 입력하거나 추천 키워드를 클릭하여 최신 뉴스를 확인해보세요!")


# 사이드바
st.sidebar.header("ℹ️ 사용 가이드")
st.sidebar.markdown("""
- **검색어 직접 입력**: 원하는 키워드를 입력하고 '뉴스 검색' 버튼을 누르세요.
- **추천 키워드**: 제공된 버튼을 클릭하면 해당 키워드로 즉시 뉴스를 검색합니다.
- **결과 캐싱**: 동일한 검색어에 대해서는 1시간 동안 검색 결과가 캐시되어 빠르게 제공됩니다.
- **뉴스 출처**: 네이버 뉴스 API를 통해 제공됩니다.

🍊 신선한 감귤 정보, 지금 바로 확인하세요!
""")
st.sidebar.markdown("---")
st.sidebar.caption("ICB Basic_2팀")
