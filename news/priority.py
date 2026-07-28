from typing import List
from news.models import Article
from settings import MAX_ARTICLES_PER_COUNTRY


def mark_samsung_fire_direct(articles: List[Article]) -> None:
    for a in articles:
        text = f"{a.title} {a.raw_snippet}".lower()
        a.is_samsung_fire_direct = ("samsung fire" in text) or (a.keyword_tag == "samsung_fire")


def sort_and_cap(articles: List[Article]) -> List[Article]:
    """priority_rank(①~⑤) 오름차순, 동일 순위 내에서는 최신순으로 정렬 후 국가별 최대 5건으로 컷."""
    def sort_key(a: Article):
        return (a.priority_rank, -(_ts(a.published_at)))

    def _ts(iso: str) -> float:
        if not iso:
            return 0.0
        try:
            from dateutil import parser as dp
            return dp.parse(iso).timestamp()
        except (ValueError, TypeError):
            return 0.0

    sorted_articles = sorted(articles, key=sort_key)
    return sorted_articles[:MAX_ARTICLES_PER_COUNTRY]
