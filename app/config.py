from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
API_KEY_PATH = BASE_DIR / "api-key"

# OpenAI API Key 우선순위: 환경변수 > 파일
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY and API_KEY_PATH.exists():
    OPENAI_API_KEY = API_KEY_PATH.read_text(encoding="utf-8").strip()

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "chat_db")

FRONTEND_ORIGINS = [
    os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000"),
]

APP_TITLE = "My App API"
APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")
APP_PORT = int(os.environ.get("APP_PORT", 8000))
# 개발 중 연결 안정성을 위해 reload 기본값을 False로 설정
DEBUG_RELOAD = os.environ.get("DEBUG_RELOAD", "0") == "1"
