import streamlit as st
import requests
from datetime import datetime
import html

st.set_page_config(page_title="🍊 감귤 스마트 뉴스 대시보드", page_icon="🍊", layout="wide")

client_id = st.secrets["NAVER_CLIENT_ID"]
client_secret = st.secrets["NAVER_CLIENT_SECRET"]

# ✅ 네이버 뉴스 API + 캐싱 (1시간 유지)
@st.cache_data(ttl=3600)
def get_naver_news(query, display=10):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    params = {"query": query, "display": display, "sort": "date"}

    response = requests.get(url, headers=headers, params=params, timeout=5)
    response.raise_for_status()
    return response.json().get('items', [])

def remove_html_tags(text):
    return html.unescape(text).replace("<b>", "").replace("</b>", "")

def format_pubdate(pubdate_str):
    try:
        dt_obj = datetime.strptime(pubdate_str, '%a, %d %b %Y %H:%M:%S %z')
        return dt_obj.strftime('%Y년 %m월 %d일 %H:%M')
    except ValueError:
        return pubdate_str

# 🚀 추천 키워드 버튼
st.title("🍊 실시간 감귤 뉴스 대시보드")
st.markdown("> 네이버 뉴스 API로 감귤 관련 최신 뉴스 제공")

st.markdown("#### 추천 키워드:")
col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    if st.button("제주 감귤"): st.session_state['query_input'] = "제주 감귤"
with col_r2:
    if st.button("감귤 병해충"): st.session_state['query_input'] = "감귤 병해충"
with col_r3:
    if st.button("감귤 가격"): st.session_state['query_input'] = "감귤 가격"

# 검색 입력
query = st.text_input("🔍 검색어 입력", value=st.session_state.get('query_input', "제주 감귤"))
if st.button("📰 뉴스 가져오기", use_container_width=True):
    st.session_state['query_input'] = query
    with st.spinner(f"'{query}' 관련 뉴스를 가져오는 중..."):
        news_items = get_naver_news(query, display=20)

        if news_items:
            st.success(f"'{query}' 뉴스 검색 결과 ({len(news_items)}개)")
            for i, news in enumerate(news_items):
                title = remove_html_tags(news['title'])
                description = remove_html_tags(news['description'])
                pub_date = format_pubdate(news['pubDate'])
                main_link = news.get('originallink') if news.get('originallink') else news.get('link')

                # 뉴스 카드 스타일 개선
                with st.container(border=True):
                    st.markdown(f"### {i+1}. {title}")
                    st.caption(f"🗓️ {pub_date}")
                    if description:
                        st.markdown(f"> {description}")
                    st.markdown(f"""
                    <a href="{main_link}" target="_blank">🔗 기사 원문 읽기</a>  
                    <small>[네이버 뉴스 링크]({news.get('link')})</small>
                    """, unsafe_allow_html=True)
                    st.markdown("---")
        else:
            st.info(f"'{query}' 관련 뉴스가 없습니다.")

st.sidebar.header("ℹ️ 사용법")
st.sidebar.markdown("""
- **검색어**: 원하는 키워드 입력  
- **추천 키워드**: 버튼 클릭으로 바로 검색 가능  
- **속도 개선**: 동일 검색어 1시간 캐시 저장  
""")
