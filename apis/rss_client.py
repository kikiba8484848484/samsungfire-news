"""
1순위: 공식 RSS 피드 수집
"""
import feedparser
import requests
from datetime import datetime, timezone
from typing import List

from news.models import Article

RSS_TIMEOUT_SECONDS = 10  # 이 시간 안에 응답이 없으면 실패로 처리하고 다음 단계(GDELT)로 넘어감


def fetch_rss(feed_url: str, source_name: str, country: str,
              keyword_tag: str, priority_rank: int) -> List[Article]:
    """
    단일 RSS 피드에서 기사 목록을 가져온다. 실패 시 예외를 던진다 (fallback_manager가 처리).
    feedparser.parse(url)을 직접 쓰면 응답이 느린 서버에서 무한정 대기할 수 있어,
    requests로 먼저 타임아웃을 걸고 받아온 내용을 feedparser로 파싱한다.
    """
    try:
        resp = requests.get(
            feed_url,
            timeout=RSS_TIMEOUT_SECONDS,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SamsungFireNewsBot/1.0)"},
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"RSS request failed for {feed_url}: {e}")

    parsed = feedparser.parse(resp.content)

    if parsed.bozo and not parsed.entries:
        # 파싱 자체가 완전히 실패한 경우 (형식 오류 등)
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
