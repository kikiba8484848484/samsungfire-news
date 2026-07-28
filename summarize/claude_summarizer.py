"""
기사 본문(raw_snippet)만을 근거로 3~4문장 요약 + 중요도(1~5)를 산정한다.
추측/의견 삽입 금지. raw_snippet이 비어있으면(GDELT는 본문 미제공) 제목만으로
최소한의 사실 기반 요약을 생성하되, 본문이 없다는 한계를 명확히 인지시킨다.
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
출력은 반드시 아래 JSON 형식만 반환하세요 (설명, 코드블록 없이 JSON만):
{"summary": "3~4문장 요약", "importance": 1~5 중 정수, "why_important": "삼성화재 해외사업 관점에서 왜 중요한지 1문장"}
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
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text").strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)

        article.summary = data.get("summary", "").strip()
        article.importance_stars = int(data.get("importance", 3))
        article.why_important = data.get("why_important", "").strip()
    except Exception as e:
        logger.error(f"요약 실패 ({article.url}): {e}")
        article.summary = "요약 생성 실패 (원문 링크를 참고하세요)."
        article.importance_stars = 1
        article.why_important = "-"


def summarize_all(articles_by_country: dict) -> None:
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY가 없어 요약을 건너뜁니다.")
        return

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    for country, articles in articles_by_country.items():
        for article in articles:
            summarize_article(client, article)
