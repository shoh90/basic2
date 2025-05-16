import streamlit as st
import requests

# ✅ Streamlit secrets에서 안전하게 가져오기
client_id = st.secrets["NAVER_CLIENT_ID"]
client_secret = st.secrets["NAVER_CLIENT_SECRET"]

# 네이버 뉴스 검색 함수
def get_naver_news(query, display=10):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": query,
        "display": display,
        "sort": "date"
    }

    response = requests.get(url, headers=headers, params=params)
    result = response.json()

    return result.get('items', [])

# Streamlit 화면 구성
st.title("🍊 감귤 관련 실시간 뉴스 (네이버 API)")

query = st.text_input("검색어 입력", "제주 감귤")

if st.button("뉴스 가져오기"):
    with st.spinner("뉴스를 불러오는 중..."):
        try:
            news_items = get_naver_news(query)

            for news in news_items:
                # HTML 태그 제거 (네이버는 <b> 태그 씀)
                title = news['title'].replace("<b>", "").replace("</b>", "")
                st.subheader(title)
                st.write(f"🗓️ {news['pubDate']}")
                st.write(f"[뉴스 바로가기]({news['link']})")
                st.markdown("---")

        except Exception as e:
            st.error(f"오류 발생: {e}")
