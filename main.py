import logging
import sys
from datetime import datetime

from settings import LOG_DIR
from news.collector import collect_all
from news.dedup import save_seen_urls, load_seen_urls
from news.prepare import prepare_for_render
from news.priority import finalize_after_summary, top_1_per_country, top_n_overall
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

    # 1. 수집 (국가별, RSS -> GDELT -> NewsAPI fallback, 요약 전 넉넉히 후보 확보)
    candidates_by_country = collect_all()
    total_candidates = sum(len(v) for v in candidates_by_country.values())
    logger.info(f"총 수집 후보(1차 컷 후): {total_candidates}건")

    # 2. 요약 + 중요도 산정 (Claude API) - 후보 전체에 대해 수행
    summarize_all(candidates_by_country)

    # 3. 요약된 중요도를 기준으로 최종 선별
    #    - 중요도 3점 미만 제외
    #    - 국가별 최대 3건(PPT 기준)으로 컷
    final_by_country = {
        country: finalize_after_summary(articles)
        for country, articles in candidates_by_country.items()
    }
    total_final = sum(len(v) for v in final_by_country.values())
    logger.info(f"최종 선별(중요도 필터 적용 후): {total_final}건")

    # 4. 렌더링용 필드(현지시각 표기, 라벨) 준비 - 최종 선별된 기사에 대해서만
    prepare_for_render(final_by_country)

    # 5. 용도별 데이터 구성
    #    - PPT: 국가별 최대 3건 그대로
    #    - 이메일 본문(HTML): 국가별 가장 중요한 1건만
    #    - 개요(인포그래픽): 전체 국가 통틀어 가장 중요한 상위 5건
    email_articles = top_1_per_country(final_by_country)
    overview_articles = top_n_overall(final_by_country)

    # 6. HTML(이메일 본문) / PPTX 생성
    html_path = render_html(email_articles, overview_articles)
    pptx_path = render_pptx(final_by_country)
    logger.info(f"HTML 생성 완료: {html_path}")
    logger.info(f"PPTX 생성 완료: {pptx_path}")

    # 7. 이메일 발송
    send_report_email(html_path, pptx_path)

    # 8. 오늘 출력한 URL 저장 (내일 중복 방지) - 최종 선별 기준
    seen = load_seen_urls()
    for articles in final_by_country.values():
        seen.update(a.url for a in articles if a.url)
    save_seen_urls(seen)

    logger.info(f"===== 실행 완료. 로그 파일: {log_file} =====")


if __name__ == "__main__":
    main()
