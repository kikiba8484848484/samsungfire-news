# 삼성화재 해외사업 뉴스 카드뉴스 자동 생성기

매일 삼성화재 해외 진출국(미국, 영국/유럽, 싱가포르, 베트남, 인도네시아, 중국)의
"현지 언론" 보험·산업·경제 뉴스를 자동 수집하여 HTML 카드뉴스와 PowerPoint를
생성하고, 이메일로 발송합니다. 국내(한국) 언론은 사용하지 않습니다.

## 1. 전체 구조 요약

- 수집: 공식 RSS → GDELT DOC 2.0 API → NewsAPI.org 순으로 자동 fallback
- 필터: 각국 현지 시간 기준 최근 24시간 이내 기사만 채택, 발행시각 불명확 기사 제외
- 중복 제거: 동일 사건 다중 보도 시 신뢰도 높은 원문 1건만 채택, 전일 출력 URL 재출력 방지
- 요약: Claude API로 기사 본문 기반 3~4문장 요약 + 중요도(★1~5) 산정 (추측 금지)
- 출력: 국가별 최대 5건, HTML 카드뉴스 + PPTX 동시 생성
- 발송: Gmail SMTP로 본인 이메일에 HTML 본문 + PPTX 첨부 자동 발송
- 자동 실행: GitHub Actions (매일 KST 08:00)

## 2. 로컬 설치 및 테스트 방법

```bash
# 1) 저장소 클론 후 이동
cd project

# 2) 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate        # Windows는 venv\Scripts\activate

# 3) 패키지 설치
pip install -r requirements.txt

# 4) 환경변수 설정 (.env 파일을 직접 만들어 사용 - 절대 git에 커밋하지 말 것)
export ANTHROPIC_API_KEY="sk-ant-..."
export NEWSAPI_KEY="..."          # 선택 사항 (없어도 RSS/GDELT만으로 동작)
export GMAIL_ADDRESS="you@gmail.com"
export GMAIL_APP_PASSWORD="16자리 앱 비밀번호"
export RECEIVER_EMAIL="you@gmail.com"

# 5) 실행
python main.py
```

실행 결과는 `output/html/`, `output/pptx/`, `logs/`에 생성됩니다.

## 3. API 키 발급 방법

### (1) Anthropic API Key (필수 - 요약 생성용)
1. https://console.anthropic.com 접속 후 로그인/가입
2. 좌측 메뉴 `API Keys` → `Create Key`
3. 생성된 키를 `ANTHROPIC_API_KEY`로 사용

### (2) NewsAPI Key (선택 - 최종 백업용)
1. https://newsapi.org/register 에서 무료 가입
2. 발급받은 키를 `NEWSAPI_KEY`로 사용
3. 무료 티어는 하루 100회 요청 제한이 있으므로, RSS/GDELT가 정상 동작하면 거의 호출되지 않습니다.

### (3) Gmail 앱 비밀번호 (이메일 발송용)
1. Google 계정 → 보안 → **2단계 인증**을 먼저 활성화
2. https://myaccount.google.com/apppasswords 접속
3. 앱 이름을 입력하고 16자리 앱 비밀번호 생성
4. 일반 Gmail 로그인 비밀번호가 아닌, 이 16자리 값을 `GMAIL_APP_PASSWORD`로 사용

## 4. GitHub Actions 자동화 설정 (매일 오전 8시)

1. 이 프로젝트 폴더 전체를 GitHub 저장소에 push합니다.
2. 저장소 `Settings → Secrets and variables → Actions → New repository secret`에서
   아래 5개를 등록합니다.
   - `ANTHROPIC_API_KEY`
   - `NEWSAPI_KEY` (선택)
   - `GMAIL_ADDRESS`
   - `GMAIL_APP_PASSWORD`
   - `RECEIVER_EMAIL`
3. `.github/workflows/daily-news.yml`이 저장소에 포함되어 있으면 자동으로 스케줄이 등록됩니다.
   (cron: `0 23 * * *` = UTC 23:00 = KST 08:00)
4. 저장소 `Actions` 탭에서 `Daily Samsung Fire Overseas News Card` 워크플로우를 확인할 수 있습니다.
5. 바로 테스트하고 싶다면 `Actions` 탭 → 해당 워크플로우 → `Run workflow` 버튼으로 수동 실행 가능합니다.
6. 실행이 끝나면 등록하신 이메일로 카드뉴스가 자동 발송되며, `Actions` 실행 결과의
   `Artifacts`에서도 HTML/PPTX/로그를 다운로드할 수 있습니다.

> 참고: GitHub Actions 무료 티어(퍼블릭 저장소는 무제한, 프라이빗 저장소는 매월 2,000분)
> 범위 내에서 매일 실행 시 문제없이 동작합니다.

## 5. 다른 자동 실행 방법 (참고)

- **Windows**: `automation/run_windows.bat`을 작업 스케줄러에 등록 (트리거: 매일 08:00)
- **Linux/서버**: `automation/run_cron.sh`을 crontab에 등록
  ```
  0 8 * * * /bin/bash /path/to/project/automation/run_cron.sh
  ```
- 로컬/서버 방식은 컴퓨터가 항상 켜져 있어야 하므로, 현재 선택하신 **GitHub Actions 방식을 권장**합니다.

## 6. 소스 및 설정 변경

- 국가별 언론사/RSS/규제기관 목록: `settings.py`의 `COUNTRY_SOURCES` (참고 문서: `config/sources.yaml`)
- 국내 언론 차단 키워드: `settings.py`의 `BLOCKED_DOMAINS_KEYWORDS`
- 검색 우선순위(①~⑤): `settings.py`의 `SEARCH_KEYWORD_GROUPS`
- 국가별 최대 출력 건수: `settings.py`의 `MAX_ARTICLES_PER_COUNTRY` (기본 5)
- 조회 기간(현지 기준): `settings.py`의 `LOOKBACK_HOURS` (기본 24)

## 7. 알려진 제약

- Reuters, Bloomberg는 공식 공개 RSS가 사실상 중단되어 있어, 두 언론사 기사는
  GDELT DOC API의 domain 필터(`domainis:reuters.com` 등)로 수집합니다.
- GDELT DOC API는 기사 본문 전체를 제공하지 않으므로(제목/메타데이터만), 이 경로로 수집된
  기사는 요약 시 제목 기반의 최소한의 사실만 정리됩니다. 더 상세한 요약이 필요하면
  해당 언론사의 RSS 피드가 있는 경우 그 경로를 우선 사용하도록 `settings.py`에서 조정하세요.
- NewsAPI 무료 티어는 상업적 이용이 제한되므로, 사내 참고용으로만 사용하세요.
