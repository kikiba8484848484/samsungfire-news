"""
중복 기사 제거:
1) 같은 사건(제목 유사)을 여러 언론이 보도 -> 신뢰도 높은 원문 1건만 사용
2) 국내 언론 도메인 차단
3) 전날 이미 출력한 URL 재출력 방지 (config/seen_urls.json)
"""
import json
import difflib
from typing import List
from pathlib import Path

from news.models import Article
from settings import BLOCKED_DOMAINS_KEYWORDS, SEEN_URLS_PATH

# 소스 신뢰도 우선순위 (숫자가 작을수록 우선 채택)
SOURCE_TRUST_RANK = {
    "reuters.com": 1, "apnews.com": 1, "bloomberg.com": 1, "afp.com": 1,
    "ft.com": 2, "wsj.com": 2, "economist.com": 2,
}


def _trust_rank(domain: str) -> int:
    for key, rank in SOURCE_TRUST_RANK.items():
        if key in domain:
            return rank
    return 5


def block_domestic_sources(articles: List[Article]) -> List[Article]:
    def is_blocked(a: Article) -> bool:
        d = (a.domain or "").lower()
        u = (a.url or "").lower()
        return any(k in d or k in u for k in BLOCKED_DOMAINS_KEYWORDS)

    return [a for a in articles if not is_blocked(a)]


def load_seen_urls() -> set:
    if not SEEN_URLS_PATH.exists():
        return set()
    try:
        with open(SEEN_URLS_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError):
        return set()


def save_seen_urls(urls: set) -> None:
    SEEN_URLS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_URLS_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(urls), f, ensure_ascii=False, indent=2)


def remove_previously_seen(articles: List[Article]) -> List[Article]:
    seen = load_seen_urls()
    return [a for a in articles if a.url not in seen]


def dedup_same_event(articles: List[Article], title_similarity_threshold: float = 0.75) -> List[Article]:
    """제목 유사도가 높으면 같은 사건으로 간주, 신뢰도 높은 소스 1건만 남긴다."""
    kept: List[Article] = []

    # URL 완전 중복 우선 제거
    seen_urls = set()
    unique_by_url = []
    for a in articles:
        if a.url and a.url not in seen_urls:
            seen_urls.add(a.url)
            unique_by_url.append(a)

    for a in unique_by_url:
        duplicate_idx = None
        for i, existing in enumerate(kept):
            ratio = difflib.SequenceMatcher(None, a.title.lower(), existing.title.lower()).ratio()
            if ratio >= title_similarity_threshold:
                duplicate_idx = i
                break

        if duplicate_idx is None:
            kept.append(a)
        else:
            # 더 신뢰도 높은 소스로 교체
            if _trust_rank(a.domain) < _trust_rank(kept[duplicate_idx].domain):
                kept[duplicate_idx] = a

    return kept
