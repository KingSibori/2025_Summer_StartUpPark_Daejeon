@echo off
echo ========================================
echo    AI Chat 가상환경 활성화
echo ========================================
echo.

if exist "venv\Scripts\Activate.ps1" (
    echo 가상환경을 활성화합니다...
    call venv\Scripts\Activate.ps1
    echo.
    echo 가상환경이 활성화되었습니다!
    echo 이제 다음 명령어로 백엔드를 실행할 수 있습니다:
    echo   python backend.py
    echo.
    echo 또는 다음 명령어로 프론트엔드를 실행할 수 있습니다:
    echo   cd frontend
    echo   npm start
    echo.
) else (
    echo [오류] 가상환경이 존재하지 않습니다.
    echo python -m venv venv 를 실행하여 가상환경을 생성하세요.
)

pause
