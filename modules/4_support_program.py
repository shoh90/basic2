import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="지원사업 안내", layout="wide", page_icon="📝")

st.title("📝 제주 농업 지원사업 안내")

# 크롤링 대상 URL & 제도명
targets = [
    {"url": "https://agri.jeju.go.kr", "제도명": "감귤원 간벌사업"},
    {"url": "https://www.jeju.go.kr", "제도명": "노지감귤 가격안정관리제"},
    {"url": "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/view.do?pblancId=PBLN_000000000102468", "제도명": "FTA기금 과수(감귤) 고품질 시설현대화 지원사업"},
    {"url": "https://blog.naver.com/happyjejudo/223773326101", "제도명": "감귤 전정가지 파쇄 지원"},
    {"url": "https://blog.naver.com/happyjejudo/223325069685", "제도명": "농업기술보급 시범사업"},
]

# ✅ 크롤링 함수 (캐시 적용)
@st.cache_data(ttl=3600)
def fetch_support_programs():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Whale/4.31.304.16 Safari/537.36"
    }

    data = []

    for item in targets:
        url, title = item["url"], item["제도명"]
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            texts = soup.get_text(separator='\n')
            cleaned = "\n".join([line.strip() for line in texts.splitlines() if line.strip()])
            summary = cleaned[:200] + "..."

            if '제주시' in cleaned:
                기관 = "제주시"
            elif '서귀포시' in cleaned:
                기관 = "서귀포시"
            elif any(x in cleaned for x in ['농식품부', '농림축산식품부']):
                기관 = "농림축산식품부"
            elif '농업기술원' in cleaned:
                기관 = "제주특별자치도 농업기술원"
            else:
                기관 = "제주특별자치도청"

            data.append({
                "지원 제도 이름": title,
                "주요 내용": summary,
                "주관 기관": 기관,
                "출처": url
            })

        except Exception as e:
            st.error(f"❗ {title} : 데이터를 불러오는 중 오류 발생 ({e})")
            data.append({
                "지원 제도 이름": title,
                "주요 내용": "내용을 불러올 수 없습니다.",
                "주관 기관": "정보 없음",
                "출처": url
            })

    return pd.DataFrame(data)

# ✅ 데이터 로딩
df = fetch_support_programs()

# ✅ 카드형 리스트 (expander 형태)
for _, row in df.iterrows():
    with st.expander(f"✅ {row['지원 제도 이름']} ({row['주관 기관']})"):
        st.write(row['주요 내용'])
        st.markdown(f"[🔗 자세히 보기]({row['출처']})")

# ✅ 전체 표 보기
st.divider()
with st.expander("전체 목록 보기 (표 형태)"):
    st.dataframe(df, use_container_width=True)
