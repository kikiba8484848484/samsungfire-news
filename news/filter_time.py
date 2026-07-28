"""
각 국가의 현지 시간 기준 '최근 24시간' 필터.
발행 시각이 확인되지 않는 기사는 제외한다.
"""
from datetime import datetime, timedelta
from dateutil import parser as dateparser
import pytz
from typing import List

from news.models import Article
from settings import COUNTRY_TIMEZONES, LOOKBACK_HOURS


def filter_recent_24h(articles: List[Article]) -> List[Article]:
    kept = []
    for a in articles:
        if not a.published_at:
            continue  # 시각 미확인 -> 제외

        try:
            dt = dateparser.parse(a.published_at)
        except (ValueError, TypeError):
            continue

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)

        tz_name = COUNTRY_TIMEZONES.get(a.country, "UTC")
        local_tz = pytz.timezone(tz_name)
        local_now = datetime.now(local_tz)
        local_dt = dt.astimezone(local_tz)

        if local_now - timedelta(hours=LOOKBACK_HOURS) <= local_dt <= local_now:
            kept.append(a)

    return kept
