"""
전역 설정 파일
- API 키는 반드시 환경변수(GitHub Secrets)로부터 읽는다. 코드에 직접 입력하지 않는다.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ------------------------------------------------------------------
# API 키 (GitHub Secrets -> 환경변수로 주입됨)
# ------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")  # 없어도 동작 (최종 백업 단계만 스킵됨)

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "").strip()
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "").strip()

CLAUDE_MODEL = "claude-sonnet-4-6"

# ------------------------------------------------------------------
# 경로
# ------------------------------------------------------------------
OUTPUT_HTML_DIR = BASE_DIR / "output" / "html"
OUTPUT_PPTX_DIR = BASE_DIR / "output" / "pptx"
LOG_DIR = BASE_DIR / "logs"
SEEN_URLS_PATH = BASE_DIR / "config" / "seen_urls.json"
SOURCES_YAML_PATH = BASE_DIR / "config" / "sources.yaml"
TEMPLATE_DIR = BASE_DIR / "templates"

for d in (OUTPUT_HTML_DIR, OUTPUT_PPTX_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# 국가별 타임존 (현지 시간 24시간 기준 판단에 사용)
# ------------------------------------------------------------------
COUNTRY_TIMEZONES = {
    "미국": "America/New_York",
    "영국/유럽": "Europe/London",
    "싱가포르": "Asia/Singapore",
    "베트남": "Asia/Ho_Chi_Minh",
    "인도네시아": "Asia/Jakarta",
    "중국": "Asia/Shanghai",
}

# ------------------------------------------------------------------
# 국내(한국) 언론 차단 도메인 - GDELT/NewsAPI 결과에서 무조건 제외
# ------------------------------------------------------------------
BLOCKED_DOMAINS_KEYWORDS = [
    ".co.kr", ".kr", "chosun.com", "donga.com", "joongang.co.kr", "hani.co.kr",
    "yna.co.kr", "mk.co.kr", "hankyung.com", "sedaily.com", "edaily.co.kr",
    "newsis.com", "yonhapnews", "kbs.co.kr", "sbs.co.kr", "mbc.co.kr",
    "insurancenews.co.kr", "fntimes.com", "newspim.com",
]

# ------------------------------------------------------------------
# 국가별 허용 소스 (뉴스 도메인) - GDELT domain 필터 및 RSS 매칭에 사용
# ------------------------------------------------------------------
COUNTRY_SOURCES = {
    "미국": {
        "rss": {
            "WSJ Markets": "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
            "CNBC Business": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147",
            "Fortune": "https://fortune.com/feed/",
        },
        "domains": ["wsj.com", "cnbc.com", "fortune.com", "businessinsider.com",
                     "reuters.com", "apnews.com", "bloomberg.com", "afp.com"],
        "regulators": {
            "Federal Reserve": "https://www.federalreserve.gov/feeds/press_all.xml",
            "NAIC": "https://content.naic.org/rss.xml",
        },
    },
    "영국/유럽": {
        "rss": {
            "Financial Times": "https://www.ft.com/rss/home",
            "Euronews Business": "https://www.euronews.com/rss?level=theme&name=business",
        },
        "domains": ["ft.com", "economist.com", "euronews.com",
                     "reuters.com", "apnews.com", "bloomberg.com", "afp.com"],
        "regulators": {
            "Bank of England / PRA": "https://www.bankofengland.co.uk/rss/news",
            "FCA": "https://www.fca.org.uk/news/rss.xml",
        },
    },
    "싱가포르": {
        "rss": {
            "CNA Business": "https://www.channelnewsasia.com/rssfeeds/8395986",
            "Business Times": "https://www.businesstimes.com.sg/rss/singapore",
        },
        "domains": ["channelnewsasia.com", "businesstimes.com.sg",
                     "reuters.com", "apnews.com", "bloomberg.com", "afp.com"],
        "regulators": {
            "MAS": "https://www.mas.gov.sg/rss-feed",
        },
    },
    "베트남": {
        "rss": {
            "Vietnam News": "https://vietnamnews.vn/rss/economy.rss",
            "VnExpress International": "https://e.vnexpress.net/rss/business.rss",
            "Vietnam Investment Review": "https://vir.com.vn/rss/home.rss",
        },
        "domains": ["vietnamnews.vn", "e.vnexpress.net", "vir.com.vn",
                     "reuters.com", "apnews.com", "bloomberg.com", "afp.com"],
        "regulators": {
            "State Bank of Vietnam": "https://sbv.gov.vn/webcenter/portal/en/home/sbv/news/rss",
        },
    },
    "인도네시아": {
        "rss": {
            "Jakarta Post": "https://www.thejakartapost.com/rss",
            "Antara News": "https://en.antaranews.com/rss/business.xml",
        },
        "domains": ["thejakartapost.com", "antaranews.com",
                     "reuters.com", "apnews.com", "bloomberg.com", "afp.com"],
        "regulators": {
            "OJK": "https://www.ojk.go.id/en/berita-dan-kegiatan/siaran-pers/default.aspx",
        },
    },
    "중국": {
        "rss": {
            "Xinhua": "http://www.xinhuanet.com/english/rss/bizrss.xml",
            "China Daily Business": "https://www.chinadaily.com.cn/rss/business_rss.xml",
        },
        "domains": ["xinhuanet.com", "chinadaily.com.cn", "caixinglobal.com",
                     "reuters.com", "apnews.com", "bloomberg.com", "afp.com"],
        "regulators": {
            "PBOC": "http://www.pbc.gov.cn/rss/rss.xml",
        },
    },
}

# ------------------------------------------------------------------
# 검색 우선순위 키워드 (① ~ ⑤)
# ------------------------------------------------------------------
SEARCH_KEYWORD_GROUPS = [
    {"tag": "samsung_fire", "label": "삼성화재 관련 뉴스",
     "keywords": ["Samsung Fire", "Samsung Fire & Marine Insurance"]},
    {"tag": "global_insurance", "label": "글로벌 보험산업 뉴스",
     "keywords": ["insurance industry", "insurer", "reinsurance", "insurance regulation"]},
    {"tag": "samsung_group", "label": "삼성그룹 계열사 뉴스",
     "keywords": ["Samsung Electronics", "Samsung C&T", "Samsung SDI", "Samsung Group"]},
    {"tag": "regulator", "label": "금융당국 발표",
     "keywords": ["central bank", "insurance regulator", "financial supervisory"]},
    {"tag": "economy", "label": "경제·산업 뉴스",
     "keywords": ["Korean company", "economy", "market"]},
]

MAX_ARTICLES_PER_COUNTRY = 5
LOOKBACK_HOURS = 24
