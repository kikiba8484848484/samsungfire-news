"""
기사 본문(raw_snippet)만을 근거로 3~4문장 요약과 두 종류의 중요도를 산정한다.
추측/의견 삽입 금지. raw_snippet이 비어있으면(GDELT는 본문 미제공) 제목만으로
최소한의 사실 기반 요약을 생성하되, 본문이 없다는 한계를 명확히 인지시킨다.

두 종류의 점수를 한 번의 API 호출로 함께 받는다 (비용/속도를 위해 호출을 늘리지 않음):
1) importance: 삼성화재 해외사업 관련성 기준 중요도 (기존 카드뉴스 선별에 사용)
2) local_significance: 삼성화재 관련성과 무관하게, 해당 국가의 정치/경제/사건사고
   관점에서 얼마나 주목할 만한 뉴스인지 (재보험 언더라이팅 등 현지 정세 파악용,
   국가별 TOP 1건 추출에 사용)
"""
import json
import logging
from typing import List

import anthropic

from news.models import Article
from settings import ANTHROPIC_API_KEY, CLAUDE_MODEL

logger = logging.getLogger("summarizer")

SYSTEM_PROMPT = """당신은 삼성화재 해외사업 담당자를 위한 뉴스 요약가입니다.
반드시 제공된 기사 제목과 본문(있는 경우)만 근거로 사용하고, 추측하거나 배경지식을 덧붙이지 마세요.
본문이 없고 제목만 있는 경우, 제목에서 확인 가능한 사실만 짧게 정리하고 과장하지 마세요.

이 기사에 대해 서로 다른 두 가지 관점의 점수를 각각 매겨야 합니다.

[관점 1] importance (삼성화재 업무 관련성, 1~5점)
5점: 삼성화재를 직접 언급하는 기사
4점: 삼성화재 해외 보험사업(현지 보험산업, 재보험, 보험 규제/감독, 보험사 실적/M&A)과 직접 관련된 기사
3점: 삼성그룹 계열사 뉴스, 또는 해당국 중앙은행/금융당국의 정책(금리, 통화정책, 자본규제 등)처럼
      삼성화재의 투자/리스크 관리에 참고가 될 만한 기사
2점 이하: 삼성화재의 보험/투자 업무와 관련성이 낮은 일반 경제·산업 뉴스
위 기준에서 2점 이하로 판단되는 기사는 낮은 점수를 정직하게 매기세요. 관련성을 억지로 높게 주지 마세요.

[관점 2] local_significance (해당 국가의 정치/경제/사건사고 관점 중요도, 1~5점)
삼성화재와의 관련성은 완전히 무시하고, 순수하게 "이 뉴스가 그 나라의 정치·경제 상황이나
주요 사건사고(자연재해, 대형사고, 정정불안, 주요 정책 변화 등)를 이해하는 데 얼마나 중요한가"만 평가하세요.
5점: 국가 전체에 영향을 주는 매우 중대한 사건(대형 재해/사고, 정권 관련 사태, 급격한 경제 위기 등)
3점: 해당국 정치/경제에 의미 있는 영향이 있는 사건
1점: 사소하거나 지역적으로 영향이 제한적인 사건

출력은 반드시 아래 JSON 형식만 반환하세요 (설명, 코드블록 없이 JSON만):
{"headline_ko": "영문 헤드라인을 한국어로 간단히 번역한 한 줄",
 "summary": "3~4문장 요약",
 "importance": 1~5 중 정수,
 "why_important": "삼성화재 해외사업 관점에서 왜 중요한지 1문장",
 "local_significance": 1~5 중 정수,
 "why_notable_locally": "현지 정치/경제/사건사고 관점에서 왜 주목할 만한지 1문장"}
"""


def summarize_article(client: anthropic.Anthropic, article: Article) -> None:
    user_content = (
        f"국가: {article.country}\n"
        f"제목: {article.title}\n"
        f"본문 발췌: {article.raw_snippet if article.raw_snippet else '(본문 없음, 제목만 제공됨)'}\n"
    )

    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text").strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)

        article.headline_ko = data.get("headline_ko", "").strip()
        article.summary = data.get("summary", "").strip()
        article.importance_stars = int(data.get("importance", 3))
        article.why_important = data.get("why_important", "").strip()
        article.local_significance = int(data.get("local_significance", 1))
        article.why_notable_locally = data.get("why_notable_locally", "").strip()
    except Exception as e:
        logger.error(f"요약 실패 ({article.url}): {e}")
        article.headline_ko = ""
        article.summary = "요약 생성 실패 (원문 링크를 참고하세요)."
        article.importance_stars = 1
        article.why_important = "-"
        article.local_significance = 1
        article.why_notable_locally = "-"


def summarize_all(articles_by_country: dict) -> None:
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY가 없어 요약을 건너뜁니다.")
        return

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    for country, articles in articles_by_country.items():
        for article in articles:
            summarize_article(client, article)
