from pathlib import Path
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Database: Supports Postgres pgvector and local SQLite
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/docuquery.db"
    POSTGRES_DB: str = "docuquery"
    POSTGRES_USER: str = "docuquery"
    POSTGRES_PASSWORD: str = "docuquery_password"
    POSTGRES_PORT: int = 5432

    # Embedded Graph DB Path
    KUZU_DB_PATH: str = str(PROJECT_ROOT / "data" / "kuzu.db")

    # Uploads and files
    UPLOAD_DIR: str = str(PROJECT_ROOT / "data" / "uploads")
    MAX_FILE_SIZE_MB: int = 20

    # LLM Settings (Gemini 3.8 Flash via google-genai)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Embedding and Reranker
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    RERANKER_MODEL: str = "ms-marco-TinyBERT-L-2-v2"

    @field_validator("UPLOAD_DIR", "KUZU_DB_PATH", mode="after")
    @classmethod
    def resolve_paths(cls, v: str) -> str:
        p = Path(v)
        if not p.is_absolute():
            return str((PROJECT_ROOT / p).resolve())
        return str(p.resolve())

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
