#!/bin/bash
# Linux cron으로 로컬/서버에서 실행할 경우 사용하는 스크립트 (참고용)
# crontab -e 에 아래 한 줄 추가 (매일 KST 08:00):
#   0 8 * * * /bin/bash /path/to/project/automation/run_cron.sh >> /path/to/project/logs/cron.log 2>&1

cd "$(dirname "$0")/.." || exit 1

# .env 파일이 있다면 환경변수로 로드 (직접 만들어 사용, 저장소에는 커밋하지 말 것)
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

source venv/bin/activate 2>/dev/null

python3 main.py
