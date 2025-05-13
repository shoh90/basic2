# 제주/남도 기후 대시보드 (일조 포함 고도화)
> 온도, 강수량, 일조시간, 일사량 기반 감귤 최적 재배 환경 시뮬레이터

## 📂 폴더 구조
- data/: asos_weather.db, sunshine_data.csv 등
- modules/: 데이터 로딩, 가공 함수
- pages/: Streamlit 다중 페이지 (지점별, 일조, 이상기후 등)
- assets/: 로고, 아이콘 등
- app.py: 메인 Streamlit 실행파일

## 🚀 실행 방법
```bash
pip install -r requirements.txt
streamlit run app.py
