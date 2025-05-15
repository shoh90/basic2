import pandas as pd

def get_today_weather_summary(df):
    """
    오늘 날짜 기준 기온, 강수량, 풍속 요약
    """
    today = df['일시'].max()
    today_data = df[df['일시'] == today]
    if today_data.empty:
        return {"평균기온": 0, "일강수량": 0, "평균풍속": 0}

    result = {
        "평균기온": today_data['평균기온(°C)'].values[0],
        "일강수량": today_data['일강수량(mm)'].values[0],
        "평균풍속": today_data['평균 풍속(m/s)'].values[0]
    }
    return result

def get_top_pest_disease(df, crop, region, month, top_n=5):
    """
    특정 작물, 지역, 월 기준 병해충 TOP N
    """
    filtered = df[
        (df['작물명'] == crop) &
        (df['지역명'] == region) &
        (df['월'] == month)
    ]
    top = filtered['병해충명'].value_counts().head(top_n).reset_index()
    top.columns = ['병해충명', '발생건수']
    return top

def get_monthly_pest_trend(df, crop, region):
    """
    작물, 지역 기준 월별 평균 위험도 추이
    """
    filtered = df[
        (df['작물명'] == crop) &
        (df['지역명'] == region)
    ]
    trend = filtered.groupby('월')['위험도지수'].mean().reset_index()
    return trend
