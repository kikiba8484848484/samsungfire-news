import logging
import sys
from datetime import datetime

from settings import LOG_DIR
from news.collector import collect_all
from news.dedup import save_seen_urls, load_seen_urls
from news.prepare import prepare_for_render
from news.priority import finalize_after_summary, top_1_per_country, top1_local_affairs_per_country
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

    candidates_by_country = collect_all()
    total_candidates = sum(len(v) for v in candidates_by_country.values())
    logger.info(f"총 수집 후보(1차 컷 후): {total_candidates}건")

    summarize_all(candidates_by_country)

    final_by_country = {
        country: finalize_after_summary(articles)
        for country, articles in candidates_by_country.items()
    }
    total_final = sum(len(v) for v in final_by_country.values())
    logger.info(f"최종 선별(중요도 필터 적용 후): {total_final}건")

    used_urls = {a.url for arts in final_by_country.values() for a in arts}
    local_affairs_top1 = top1_local_affairs_per_country(candidates_by_country, exclude_urls=used_urls)
    logger.info(f"현지 정세 TOP1 확보 국가 수: {len(local_affairs_top1)}개국")

    prepare_for_render(final_by_country)
    prepare_for_render({c: [a] for c, a in local_affairs_top1.items()})

    email_articles = top_1_per_country(final_by_country)

    html_path = render_html(email_articles, local_affairs_top1)
    pptx_path = render_pptx(final_by_country, local_affairs_top1)
    logger.info(f"HTML 생성 완료: {html_path}")
    logger.info(f"PPTX 생성 완료: {pptx_path}")

    send_report_email(html_path, pptx_path)

    seen = load_seen_urls()
    for articles in final_by_country.values():
        seen.update(a.url for a in articles if a.url)
    save_seen_urls(seen)

    logger.info(f"===== 실행 완료. 로그 파일: {log_file} =====")


if __name__ == "__main__":
    main()
