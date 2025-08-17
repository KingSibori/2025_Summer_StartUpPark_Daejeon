@echo off
echo ========================================
echo    AI Chat Backend 시작
echo ========================================
echo.

echo 1. 가상환경 활성화 중...
if exist "venv\Scripts\Activate.ps1" (
    call venv\Scripts\Activate.ps1
    echo 가상환경이 활성화되었습니다.
) else (
    echo [경고] 가상환경이 존재하지 않습니다.
    echo python -m venv venv 를 실행하여 가상환경을 생성하세요.
    pause
    exit /b 1
)

echo.
echo 2. Python 의존성 확인 중...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [경고] FastAPI가 설치되지 않았습니다.
    echo pip install -r requirements.txt 를 실행하세요.
    pause
    exit /b 1
)

echo 3. MongoDB 연결 확인 중...
python -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017').admin.command('ping')" >nul 2>&1
if errorlevel 1 (
    echo [경고] MongoDB에 연결할 수 없습니다.
    echo MongoDB가 실행 중인지 확인하세요.
    pause
    exit /b 1
)

echo 4. API 키 확인 중...
if not exist "api-key" (
    echo [경고] api-key 파일이 없습니다.
    echo OpenAI API 키를 api-key 파일에 설정하세요.
    pause
    exit /b 1
)

echo.
echo 모든 검사 완료! 백엔드를 시작합니다...
echo.
python backend.py
pause
