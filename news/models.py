from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Article:
    title: str
    url: str
    domain: str
    source_name: str
    published_at: Optional[str]  # ISO8601, 타임존 포함. None이면 시각 미확인
    country: str
    keyword_tag: str             # 어느 우선순위 그룹에서 검색됐는지 (samsung_fire 등)
    priority_rank: int           # 그룹 우선순위 (1~5, 낮을수록 우선)
    fetched_via: str             # "rss" | "gdelt" | "newsapi"
    raw_snippet: str = ""        # 본문 일부 (요약용, 없을 수 있음)
    is_samsung_fire_direct: bool = False

    # 요약 단계에서 채워짐
    summary: str = ""
    importance_stars: int = 0
    why_important: str = ""
    headline_ko: str = ""

    # 현지 정세(정치/경제/사건사고) 중요도 - 삼성화재 관련성과는 별개 기준
    local_significance: int = 0
    why_notable_locally: str = ""

    # 렌더링 단계에서 채워짐
    local_time_display: str = ""
    keyword_label: str = ""
