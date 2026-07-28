@echo off
REM Windows 작업 스케줄러에서 매일 오전 8시에 이 파일을 실행하도록 등록하면 됩니다 (참고용).
REM 작업 스케줄러 > 기본 작업 만들기 > 트리거: 매일 08:00 > 동작: 이 .bat 파일 실행

cd /d %~dp0\..

call venv\Scripts\activate.bat

python main.py
