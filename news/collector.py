import logging
from typing import Dict, List

from news.models import Article
from news.filter_time import filter_recent_24h
from news.dedup import block_domestic_sources, remove_previously_seen, dedup_same_event
from news.priority import mark_samsung_fire_direct, sort_and_cap
from apis.fallback_manager import collect_from_rss_feeds, collect_with_fallback
from settings import COUNTRY_SOURCES, SEARCH_KEYWORD_GROUPS, NEWSAPI_KEY

logger = logging.getLogger("collector")


def collect_for_country(country: str) -> List[Article]:
    src = COUNTRY_SOURCES.get(country)
    if not src:
        logger.warning(f"{country}: 등록된 소스 없음")
        return []

    all_articles: List[Article] = []

    # ① ~ ⑤ 우선순위 키워드 그룹 순회 (regulator 그룹은 regulator RSS도 함께 조회)
    for idx, group in enumerate(SEARCH_KEYWORD_GROUPS, start=1):
        tag, label, keywords = group["tag"], group["label"], group["keywords"]

        for kw in keywords:
            articles = collect_with_fallback(
                keyword=kw,
                domains=src["domains"],
                country=country,
                keyword_tag=tag,
                priority_rank=idx,
                rss_feeds=src.get("rss", {}),
                newsapi_key=NEWSAPI_KEY,
            )
            all_articles.extend(articles)

        # 금융당국 발표(④)는 규제기관 RSS를 직접 수집
        if tag == "regulator" and src.get("regulators"):
            all_articles.extend(
                collect_from_rss_feeds(src["regulators"], country, tag, idx)
            )

    # 일반 RSS(각 언론사 RSS)도 항상 함께 수집하여 ①~⑤ 분류 없이 최신 기사 풀에 포함
    # (수집 후 제목 매칭으로 삼성화재 직접관련 여부만 별도 표시)
    general_rss_articles = collect_from_rss_feeds(src.get("rss", {}), country,
                                                    keyword_tag="general", priority_rank=5)
    all_articles.extend(general_rss_articles)

    # 필터링 파이프라인
    all_articles = block_domestic_sources(all_articles)
    all_articles = filter_recent_24h(all_articles)
    all_articles = dedup_same_event(all_articles)
    all_articles = remove_previously_seen(all_articles)
    mark_samsung_fire_direct(all_articles)
    final_articles = sort_and_cap(all_articles)

    logger.info(f"{country}: 최종 {len(final_articles)}건 선정")
    return final_articles


def collect_all() -> Dict[str, List[Article]]:
    result = {}
    for country in COUNTRY_SOURCES.keys():
        try:
            result[country] = collect_for_country(country)
        except Exception as e:
            logger.error(f"{country} 수집 중 예상치 못한 오류: {e}")
            result[country] = []
    return result
