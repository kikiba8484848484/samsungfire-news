"""
API 장애 발생 시 로그를 남기고 다음 API로 자동 전환한다.
프로그램 전체가 중단되지 않도록 모든 단계에서 예외를 흡수한다.
"""
import logging
from typing import List

from news.models import Article
from apis.rss_client import fetch_rss
from apis.gdelt_client import fetch_gdelt
from apis.newsapi_client import fetch_newsapi

logger = logging.getLogger("fallback_manager")


def collect_from_rss_feeds(rss_feeds: dict, country: str, keyword_tag: str,
                            priority_rank: int) -> List[Article]:
    """국가에 등록된 모든 RSS 피드를 순회하며 수집. 개별 피드 실패는 스킵."""
    results = []
    for source_name, feed_url in rss_feeds.items():
        try:
            articles = fetch_rss(feed_url, source_name, country, keyword_tag, priority_rank)
            logger.info(f"[RSS 성공] {country}/{source_name}: {len(articles)}건")
            results.extend(articles)
        except Exception as e:
            logger.warning(f"[RSS 실패] {country}/{source_name}: {e}")
    return results


def collect_with_fallback(keyword: str, domains: List[str], country: str,
                           keyword_tag: str, priority_rank: int,
                           rss_feeds: dict, newsapi_key: str) -> List[Article]:
    """
    한 키워드에 대해 RSS -> GDELT -> NewsAPI 순으로 시도한다.
    RSS는 키워드 필터링이 안 되므로(피드 자체가 이미 특정 소스), 키워드 검색은
    주로 GDELT/NewsAPI가 담당하고 RSS는 별도 함수(collect_from_rss_feeds)로 항상 함께 수집한다.
    """
    # 1순위: GDELT (RSS로 커버 안 되는 Reuters/Bloomberg/AP/AFP 등 포함, 키워드 검색 가능)
    try:
        articles = fetch_gdelt(keyword, domains, country, keyword_tag, priority_rank)
        logger.info(f"[GDELT 성공] {country}/{keyword_tag}({keyword}): {len(articles)}건")
        if articles:
            return articles
        logger.info(f"[GDELT 결과없음] {country}/{keyword_tag}({keyword}) -> NewsAPI로 전환")
    except Exception as e:
        logger.warning(f"[GDELT 실패] {country}/{keyword_tag}({keyword}): {e} -> NewsAPI로 전환")

    # 최종 백업: NewsAPI
    try:
        articles = fetch_newsapi(keyword, domains, country, keyword_tag, priority_rank, newsapi_key)
        logger.info(f"[NewsAPI 성공] {country}/{keyword_tag}({keyword}): {len(articles)}건")
        return articles
    except Exception as e:
        logger.error(f"[NewsAPI 실패] {country}/{keyword_tag}({keyword}): {e} -> 이 키워드는 결과 없음 처리")
        return []
