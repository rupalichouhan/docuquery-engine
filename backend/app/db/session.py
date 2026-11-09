import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger
from app.db.models import Base

# Ensure parent directory for local db exists
os.makedirs("./data", exist_ok=True)

# Normalize database URL across drivers & platforms (Supabase, Neon, Docker)
raw_url = settings.DATABASE_URL.strip()
if raw_url.startswith("postgres://"):
    db_url = "postgresql+psycopg://" + raw_url[len("postgres://"):]
elif raw_url.startswith("postgresql+asyncpg://"):
    db_url = "postgresql+psycopg://" + raw_url[len("postgresql+asyncpg://"):]
elif raw_url.startswith("postgresql://"):
    db_url = "postgresql+psycopg://" + raw_url[len("postgresql://"):]
elif raw_url.startswith("sqlite+aiosqlite://"):
    db_url = "sqlite://" + raw_url[len("sqlite+aiosqlite://"):]
else:
    db_url = raw_url

engine = create_engine(
    db_url,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def init_db() -> None:
    """Initialize database tables."""
    try:
        if "postgresql" in db_url:
            from sqlalchemy import text
            with engine.connect() as conn:
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
                    conn.commit()
                except Exception as ext_err:
                    logger.warning(f"Vector extension check notice: {ext_err}")
        
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database schema initialized successfully with engine: {db_url}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise e

def get_db() -> Generator[Session, None, None]:
    """Dependency for yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
