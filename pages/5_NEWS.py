import streamlit as st
import requests
from datetime import datetime
import html # HTML 태그를 안전하게 제거하거나 이스케이프하기 위함

# 페이지 기본 설정
st.set_page_config(page_title="🍊 감귤 뉴스", page_icon="🍊", layout="wide")

# ✅ Streamlit secrets에서 안전하게 가져오기
try:
    client_id = st.secrets["NAVER_CLIENT_ID"]
    client_secret = st.secrets["NAVER_CLIENT_SECRET"]
except KeyError:
    st.error("네이버 API 인증 정보가 Streamlit secrets에 설정되지 않았습니다.")
    st.stop()

# 네이버 뉴스 검색 함수
def get_naver_news(query, display=10, start=1, sort="date"): # start, sort 파라미터 추가
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort # sim: 정확도순, date: 날짜순
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status() # 오류 발생 시 예외 발생
        result = response.json()
        return result.get('items', [])
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류 발생: {e}")
        return []
    except ValueError as e: # JSON 디코딩 오류
        st.error(f"API 응답 분석 중 오류 발생 (JSON 형식 오류 가능성): {e}")
        st.error(f"API Raw Response: {response.text[:500]}...") # 응답 일부 표시
        return []


# HTML 태그 제거 함수 (더 안전하게)
def remove_html_tags(text):
    return html.unescape(text).replace("<b>", "").replace("</b>", "") # 네이버는 <b> 태그 외에 다른 HTML 엔티티도 사용 가능

# 날짜 형식 변환 함수
def format_pubdate(pubdate_str):
    try:
        # 예: "Mon, 15 Jul 2024 10:00:00 +0900"
        dt_obj = datetime.strptime(pubdate_str, '%a, %d %b %Y %H:%M:%S %z')
        return dt_obj.strftime('%Y년 %m월 %d일 %H:%M')
    except ValueError:
        return pubdate_str # 파싱 실패 시 원본 반환

# Streamlit 화면 구성
st.title("🍊 실시간 감귤 뉴스 대시보드")
st.markdown("""
    네이버 뉴스 API를 활용하여 감귤 관련 최신 뉴스를 보여줍니다.
    검색어를 입력하고 '뉴스 가져오기' 버튼을 클릭하세요.
""")

# 세션 상태 초기화
if 'news_items' not in st.session_state:
    st.session_state.news_items = []
if 'searched_query' not in st.session_state:
    st.session_state.searched_query = ""
if 'search_triggered' not in st.session_state:
    st.session_state.search_triggered = False

# 검색 UI 영역 (컬럼으로 배치하여 더 깔끔하게)
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("🔍 검색어 입력", value=st.session_state.get('last_query', "제주 감귤"), key="query_input")
with col2:
    st.write("") # 버튼과 높이 맞추기 위한 빈 공간
    st.write("")
    if st.button("📰 뉴스 가져오기", use_container_width=True):
        if not query:
            st.warning("검색어를 입력해주세요.")
        else:
            st.session_state.search_triggered = True
            st.session_state.searched_query = query
            st.session_state.last_query = query # 마지막 검색어 저장
            with st.spinner(f"'{query}' 관련 뉴스를 불러오는 중..."):
                try:
                    news_items_fetched = get_naver_news(query, display=20) # 20개로 늘림
                    if news_items_fetched:
                        st.session_state.news_items = news_items_fetched
                    else:
                        st.session_state.news_items = [] # 결과 없으면 비움
                except Exception as e:
                    st.error(f"뉴스 로딩 중 오류 발생: {e}")
                    st.session_state.news_items = []


# 뉴스 표시 영역
if st.session_state.search_triggered:
    if st.session_state.news_items:
        st.subheader(f"'{st.session_state.searched_query}' 뉴스 검색 결과 ({len(st.session_state.news_items)}개)")
        st.markdown("---")

        for i, news in enumerate(st.session_state.news_items):
            with st.container(border=True):
                title = remove_html_tags(news['title'])
                description = remove_html_tags(news['description'])
                pub_date = format_pubdate(news['pubDate'])
                
                st.markdown(f"#### {i+1}. {title}")

                col_meta1, col_meta2 = st.columns([1,3])
                with col_meta1:
                    st.caption(f"🗓️ 게시일: {pub_date}")
                
                if description:
                    st.markdown(f"> {description}") # 인용구 스타일로 요약 표시

                # 링크 처리: originallink가 있으면 그것을 메인으로, 없으면 link 사용
                main_link = news.get('originallink') if news.get('originallink') else news.get('link')
                
                if main_link:
                    st.markdown(f"🔗 [기사 원문 읽기]({main_link})", unsafe_allow_html=True)
                
                # 네이버 뉴스 링크도 필요하다면 추가 (originallink와 다를 경우)
                if news.get('originallink') and news.get('link') and news['originallink'] != news['link']:
                    st.caption(f"네이버 뉴스 링크: [{news.get('link')}]({news.get('link')})")

            st.markdown("<br>", unsafe_allow_html=True) # 카드 간 간격

    elif st.session_state.searched_query: # 검색은 했는데 결과가 없을 때
        st.info(f"'{st.session_state.searched_query}'에 대한 뉴스 검색 결과가 없습니다.")
else:
    st.info("상단에서 검색어를 입력하고 '뉴스 가져오기' 버튼을 클릭하여 뉴스를 확인하세요.")

st.sidebar.header("ℹ️ 정보")
st.sidebar.markdown("""
이 앱은 네이버 검색 API를 사용하여 실시간 뉴스를 제공합니다.
- **검색어**: 원하는 키워드를 입력하세요.
- **결과 수**: 최대 20개의 뉴스가 표시됩니다.
- **정렬**: 최신순으로 정렬됩니다.

Made with Streamlit.
""")
