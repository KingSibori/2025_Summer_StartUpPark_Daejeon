# Deprecated: Use main.py (uvicorn main:app --reload)
import uvicorn
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.factory import create_app
from app.config import APP_HOST, APP_PORT, DEBUG_RELOAD

app = create_app()

if __name__ == "__main__":
    uvicorn.run("backend:app", host=APP_HOST, port=APP_PORT, reload=DEBUG_RELOAD)
