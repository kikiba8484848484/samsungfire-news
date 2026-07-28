"""
2순위: GDELT DOC 2.0 API 수집
공식 RSS가 없는 소스(Reuters, Bloomberg, AP, AFP 등) 및 키워드 기반 검색에 사용.
무료, 키 불필요. https://api.gdeltproject.org/api/v2/doc/doc
"""
import requests
from datetime import datetime, timezone
from typing import List

from news.models import Article

GDELT_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"


def fetch_gdelt(keyword: str, domains: List[str], country: str,
                 keyword_tag: str, priority_rank: int,
                 max_records: int = 20, timeout: int = 20) -> List[Article]:
    """
    특정 키워드 + 허용 도메인 목록으로 GDELT를 검색한다.
    실패 시(네트워크/HTTP 오류) 예외를 던진다.
    """
    domain_filter = " OR ".join([f"domainis:{d}" for d in domains])
    query = f"({keyword}) ({domain_filter})"

    params = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": max_records,
        "format": "json",
        "sort": "DateDesc",
    }

    resp = requests.get(GDELT_ENDPOINT, params=params, timeout=timeout)
    resp.raise_for_status()

    try:
        data = resp.json()
    except ValueError as e:
        raise RuntimeError(f"GDELT returned non-JSON response: {e}")

    articles = []
    for item in data.get("articles", []):
        # GDELT seendate 형식: "20260728T090000Z"
        seendate = item.get("seendate")
        published_iso = None
        if seendate:
            try:
                dt = datetime.strptime(seendate, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                published_iso = dt.isoformat()
            except ValueError:
                published_iso = None

        articles.append(Article(
            title=item.get("title", "").strip(),
            url=item.get("url", ""),
            domain=item.get("domain", ""),
            source_name=item.get("domain", ""),
            published_at=published_iso,
            country=country,
            keyword_tag=keyword_tag,
            priority_rank=priority_rank,
            fetched_via="gdelt",
            raw_snippet="",  # GDELT DOC API는 본문을 제공하지 않음 (제목/메타데이터만)
        ))
    return articles
