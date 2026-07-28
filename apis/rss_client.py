"""
1순위: 공식 RSS 피드 수집
"""
import feedparser
from datetime import datetime, timezone
from typing import List

from news.models import Article


def fetch_rss(feed_url: str, source_name: str, country: str,
              keyword_tag: str, priority_rank: int) -> List[Article]:
    """단일 RSS 피드에서 기사 목록을 가져온다. 실패 시 예외를 던진다 (fallback_manager가 처리)."""
    parsed = feedparser.parse(feed_url)

    if parsed.bozo and not parsed.entries:
        # 파싱 자체가 완전히 실패한 경우 (네트워크 오류 등)
        raise RuntimeError(f"RSS parse failed for {feed_url}: {parsed.bozo_exception}")

    articles = []
    for entry in parsed.entries:
        published_iso = None
        if getattr(entry, "published_parsed", None):
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            published_iso = dt.isoformat()
        elif getattr(entry, "updated_parsed", None):
            dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            published_iso = dt.isoformat()
        # published_iso가 None이면 filter_time 단계에서 "시각 미확인"으로 제외됨

        domain = entry.get("link", "").split("/")[2] if entry.get("link") else ""

        articles.append(Article(
            title=entry.get("title", "").strip(),
            url=entry.get("link", ""),
            domain=domain,
            source_name=source_name,
            published_at=published_iso,
            country=country,
            keyword_tag=keyword_tag,
            priority_rank=priority_rank,
            fetched_via="rss",
            raw_snippet=entry.get("summary", "")[:1000],
        ))
    return articles
