from dateutil import parser as dateparser
import pytz
from typing import Dict, List

from news.models import Article
from settings import COUNTRY_TIMEZONES, SEARCH_KEYWORD_GROUPS

_LABEL_BY_TAG = {g["tag"]: g["label"] for g in SEARCH_KEYWORD_GROUPS}
_LABEL_BY_TAG["general"] = "현지 언론 일반"


def prepare_for_render(articles_by_country: Dict[str, List[Article]]) -> None:
    for country, articles in articles_by_country.items():
        tz_name = COUNTRY_TIMEZONES.get(country, "UTC")
        local_tz = pytz.timezone(tz_name)
        for a in articles:
            a.keyword_label = _LABEL_BY_TAG.get(a.keyword_tag, a.keyword_tag)
            if a.published_at:
                try:
                    dt = dateparser.parse(a.published_at).astimezone(local_tz)
                    a.local_time_display = dt.strftime("%Y-%m-%d %H:%M (%Z)")
                except (ValueError, TypeError):
                    a.local_time_display = "확인 불가"
            else:
                a.local_time_display = "확인 불가"
