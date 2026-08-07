"""
2순위: GDELT DOC 2.0 API 수집
공식 RSS가 없는 소스(Reuters, Bloomberg, AP, AFP 등) 및 키워드 기반 검색에 사용.
무료, 키 불필요. https://api.gdeltproject.org/api/v2/doc/doc

GDELT는 짧은 시간에 요청이 몰리면 429(Too Many Requests)를 반환한다.
연속 호출이 많은 이 프로그램 구조상 429가 자주 발생하므로,
- 요청 사이 최소 간격을 보장하고
- 429를 받으면 잠깐 쉬었다가 재시도한다.
"""
import time
import requests
from datetime import datetime, timezone
from typing import List

from news.models import Article

GDELT_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"

MAX_RETRIES = 1
RETRY_BACKOFF_SECONDS = [3]  # 429/일시 오류 시 한 번만 짧게 재시도 (계속 실패하면 빨리 포기)
MIN_INTERVAL_SECONDS = 1.0  # 매 요청 전 최소 이 정도는 쉬어서 애초에 429를 덜 유발

_last_request_time = 0.0


def _throttle():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_INTERVAL_SECONDS:
        time.sleep(MIN_INTERVAL_SECONDS - elapsed)
    _last_request_time = time.time()


def fetch_gdelt(keyword: str, domains: List[str], country: str,
                 keyword_tag: str, priority_rank: int,
                 max_records: int = 20, timeout: int = 20) -> List[Article]:
    """
    특정 키워드 + 허용 도메인 목록으로 GDELT를 검색한다.
    429를 받으면 최대 MAX_RETRIES회까지 대기 후 재시도한다.
    그래도 실패하면 예외를 던진다 (fallback_manager가 처리).
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

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        _throttle()
        try:
            resp = requests.get(GDELT_ENDPOINT, params=params, timeout=timeout)
            if resp.status_code == 429:
                last_error = RuntimeError("429 Too Many Requests")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS[attempt])
                    continue
                raise last_error
            resp.raise_for_status()
            data = resp.json()
            break
        except requests.HTTPError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS[attempt])
                continue
            raise
        except ValueError as e:
            # JSON 파싱 실패 (GDELT가 빈 응답/HTML 에러 페이지를 준 경우) - 재시도 가치 있음
            last_error = RuntimeError(f"GDELT returned non-JSON response: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS[attempt])
                continue
            raise last_error
    else:
        raise last_error

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
