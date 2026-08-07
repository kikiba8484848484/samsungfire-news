from typing import Dict, List
from news.models import Article
from settings import (
    MAX_ARTICLES_PER_COUNTRY_COLLECT,
    MAX_ARTICLES_PER_COUNTRY,
    MIN_IMPORTANCE_STARS,
    TOP_N_OVERALL_FOR_OVERVIEW,
    LOCAL_AFFAIRS_MIN_SIGNIFICANCE,
)


def mark_samsung_fire_direct(articles: List[Article]) -> None:
    for a in articles:
        text = f"{a.title} {a.raw_snippet}".lower()
        a.is_samsung_fire_direct = ("samsung fire" in text) or (a.keyword_tag == "samsung_fire")


def _ts(iso: str) -> float:
    if not iso:
        return 0.0
    try:
        from dateutil import parser as dp
        return dp.parse(iso).timestamp()
    except (ValueError, TypeError):
        return 0.0


def sort_and_cap_precollect(articles: List[Article]) -> List[Article]:
    """
    요약 전 1차 컷. priority_rank(①~⑤) 오름차순, 동일 순위 내 최신순으로 정렬 후
    국가별로 넉넉히(MAX_ARTICLES_PER_COUNTRY_COLLECT) 남겨서 요약 이후 중요도 필터링의 여지를 준다.
    """
    def sort_key(a: Article):
        return (a.priority_rank, -_ts(a.published_at))

    sorted_articles = sorted(articles, key=sort_key)
    return sorted_articles[:MAX_ARTICLES_PER_COUNTRY_COLLECT]


def finalize_after_summary(articles: List[Article]) -> List[Article]:
    """
    요약/중요도 산정 완료 후 최종 선별.
    1) 중요도(MIN_IMPORTANCE_STARS) 미만 기사는 제외 (관련성 낮은 기사 컷)
    2) 중요도 내림차순, 동일 중요도 내에서는 priority_rank 오름차순 정렬
    3) 국가별 최대 MAX_ARTICLES_PER_COUNTRY 건으로 컷 (PPT 기준 개수)
    """
    filtered = [a for a in articles if a.importance_stars >= MIN_IMPORTANCE_STARS]
    filtered.sort(key=lambda a: (-a.importance_stars, a.priority_rank))
    return filtered[:MAX_ARTICLES_PER_COUNTRY]


def top_1_per_country(articles_by_country: Dict[str, List[Article]]) -> Dict[str, List[Article]]:
    """이메일 본문용: 국가별로 가장 중요한 기사 1건만."""
    return {country: (arts[:1] if arts else []) for country, arts in articles_by_country.items()}


def top_n_overall(articles_by_country: Dict[str, List[Article]], n: int = None) -> List[Article]:
    """인포그래픽 개요 페이지용: 전체 국가를 통틀어 가장 중요한 상위 n건."""
    if n is None:
        n = TOP_N_OVERALL_FOR_OVERVIEW
    all_articles = [a for arts in articles_by_country.values() for a in arts]
    all_articles.sort(key=lambda a: (-a.importance_stars, a.priority_rank))
    return all_articles[:n]


def top1_local_affairs_per_country(articles_by_country: Dict[str, List[Article]],
                                    min_significance: int = None) -> Dict[str, Article]:
    """
    삼성화재 관련성과 무관하게, 국가별로 '현지 정치/경제/사건사고' 관점에서
    가장 주목할 만한 기사 1건을 뽑는다. 삼성화재 관련성 필터(finalize_after_summary) 이전의
    전체 후보군을 대상으로 해야 하므로, main.py에서 요약 직후(필터링 전) 이 함수를 호출해야 한다.
    min_significance 미만인 국가는 결과에서 제외한다(억지로 채우지 않음).
    """
    if min_significance is None:
        min_significance = LOCAL_AFFAIRS_MIN_SIGNIFICANCE
    result: Dict[str, Article] = {}
    for country, articles in articles_by_country.items():
        if not articles:
            continue
        best = max(articles, key=lambda a: (a.local_significance, _ts(a.published_at)))
        if best.local_significance >= min_significance:
            result[country] = best
    return result
