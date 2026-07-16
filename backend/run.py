"""
Entry point for the backend API.
Run with: python run.py
Or:       uvicorn app.main:app --reload --port 8000
"""
import uvicorn
from app.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=settings.ENV == "development",
    )
