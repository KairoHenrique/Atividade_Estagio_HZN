import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Gemini API
    gemini_api_key: str = ""

    # Email SMTP
    smtp_email: str = ""
    smtp_password: str = ""

    # Avaliador
    evaluator_email: str = ""
    evaluator_password: str = "admin123"

    # JWT
    jwt_secret: str = "default-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Frontend URL
    frontend_url: str = "http://localhost:5173"

    # Upload
    upload_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    max_file_size_mb: int = 20
    allowed_extensions: list[str] = [".pdf", ".doc", ".docx"]

    # Database
    database_url: str = "sqlite:///./submissions.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)
