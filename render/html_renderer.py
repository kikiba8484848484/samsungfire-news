from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from settings import TEMPLATE_DIR, OUTPUT_HTML_DIR, now_kst


def render_html(articles_by_country: dict, local_affairs_top1: dict) -> Path:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("cardnews.html.j2")

    report_date = now_kst().strftime("%Y-%m-%d")
    html = template.render(
        report_date=report_date,
        countries=articles_by_country,
        local_affairs_top1=local_affairs_top1,
    )

    out_path = OUTPUT_HTML_DIR / f"cardnews_{report_date}.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path
