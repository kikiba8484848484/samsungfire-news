from datetime import datetime
from pathlib import Path
from collections import OrderedDict
from jinja2 import Environment, FileSystemLoader

from settings import TEMPLATE_DIR, OUTPUT_HTML_DIR, now_kst


def _group_by_country(overview_articles: list) -> "OrderedDict":
    """개요 기사를 국가별로 묶는다. 첫 등장 순서(중요도순)를 그대로 그룹 순서로 사용한다."""
    grouped = OrderedDict()
    for a in overview_articles:
        grouped.setdefault(a.country, []).append(a)
    return grouped


def render_html(articles_by_country: dict, overview_articles: list, local_affairs_top1: dict) -> Path:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("cardnews.html.j2")

    report_date = now_kst().strftime("%Y-%m-%d")
    html = template.render(
        report_date=report_date,
        countries=articles_by_country,
        overview_by_country=_group_by_country(overview_articles),
        local_affairs_top1=local_affairs_top1,
    )

    out_path = OUTPUT_HTML_DIR / f"cardnews_{report_date}.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path
