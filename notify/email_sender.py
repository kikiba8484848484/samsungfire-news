import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from datetime import datetime

from settings import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, RECEIVER_EMAIL

logger = logging.getLogger("email_sender")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_report_email(html_path: Path, pptx_path: Path) -> bool:
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD and RECEIVER_EMAIL):
        logger.error("이메일 발송 설정(GMAIL_ADDRESS/GMAIL_APP_PASSWORD/RECEIVER_EMAIL)이 없어 발송을 건너뜁니다.")
        return False

    # RECEIVER_EMAIL은 콤마(,)로 여러 명을 구분해서 등록 가능 (예: "a@x.com,b@y.com")
    recipients = [addr.strip() for addr in RECEIVER_EMAIL.split(",") if addr.strip()]
    if not recipients:
        logger.error("RECEIVER_EMAIL에 유효한 주소가 없어 발송을 건너뜁니다.")
        return False

    today = datetime.now()
    subject_date = today.strftime("%y%m%d")  # 예: 260729
    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"삼성화재 글로벌운영팀 카드뉴스 {subject_date}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = ", ".join(recipients)

    html_content = html_path.read_text(encoding="utf-8")
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with open(pptx_path, "rb") as f:
        part = MIMEApplication(f.read(), Name=pptx_path.name)
    part["Content-Disposition"] = f'attachment; filename="{pptx_path.name}"'
    msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, recipients, msg.as_string())
        logger.info(f"이메일 발송 성공: {recipients}")
        return True
    except Exception as e:
        logger.error(f"이메일 발송 실패: {e}")
        return False
