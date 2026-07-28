import logging
import sys
from datetime import datetime

from settings import LOG_DIR
from news.collector import collect_all
from news.dedup import save_seen_urls, load_seen_urls
from news.prepare import prepare_for_render
from summarize.claude_summarizer import summarize_all
from render.html_renderer import render_html
from render.pptx_renderer import render_pptx
from notify.email_sender import send_report_email


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return log_file


def main():
    log_file = setup_logging()
    logger = logging.getLogger("main")
    logger.info("===== 삼성화재 해외사업 뉴스 카드뉴스 생성 시작 =====")

    # 1. 수집 (국가별, RSS -> GDELT -> NewsAPI fallback)
    articles_by_country = collect_all()
    total = sum(len(v) for v in articles_by_country.values())
    logger.info(f"총 수집 기사 수(필터링 후): {total}건")

    # 2. 요약 + 중요도 산정 (Claude API)
    summarize_all(articles_by_country)

    # 3. 렌더링용 필드(현지시각 표기, 라벨) 준비
    prepare_for_render(articles_by_country)

    # 4. HTML / PPTX 생성
    html_path = render_html(articles_by_country)
    pptx_path = render_pptx(articles_by_country)
    logger.info(f"HTML 생성 완료: {html_path}")
    logger.info(f"PPTX 생성 완료: {pptx_path}")

    # 5. 이메일 발송
    send_report_email(html_path, pptx_path)

    # 6. 오늘 출력한 URL 저장 (내일 중복 방지)
    seen = load_seen_urls()
    for articles in articles_by_country.values():
        seen.update(a.url for a in articles if a.url)
    save_seen_urls(seen)

    logger.info(f"===== 실행 완료. 로그 파일: {log_file} =====")


if __name__ == "__main__":
    main()
