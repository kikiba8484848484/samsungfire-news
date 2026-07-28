"""
3순위(최종 백업): NewsAPI.org
무료 티어: 하루 100req, 최근 1개월 데이터만, 본문 전체 미제공(설명만).
RSS와 GDELT가 모두 실패했을 때만 호출된다.
"""
import requests
from typing import List

from news.models import Article

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"


def fetch_newsapi(keyword: str, domains: List[str], country: str,
                   keyword_tag: str, priority_rank: int, api_key: str,
                   page_size: int = 20, timeout: int = 20) -> List[Article]:
    if not api_key:
        raise RuntimeError("NEWSAPI_KEY가 설정되지 않아 NewsAPI를 사용할 수 없습니다.")

    params = {
        "q": keyword,
        "domains": ",".join(domains),
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": page_size,
        "apiKey": api_key,
    }

    resp = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "ok":
        raise RuntimeError(f"NewsAPI error: {data.get('message')}")

    articles = []
    for item in data.get("articles", []):
        source = item.get("source", {}) or {}
        url = item.get("url", "")
        domain = url.split("/")[2] if url and "//" in url else ""

        articles.append(Article(
            title=(item.get("title") or "").strip(),
            url=url,
            domain=domain,
            source_name=source.get("name", domain),
            published_at=item.get("publishedAt"),  # 이미 ISO8601
            country=country,
            keyword_tag=keyword_tag,
            priority_rank=priority_rank,
            fetched_via="newsapi",
            raw_snippet=(item.get("description") or "")[:1000],
        ))
    return articles
