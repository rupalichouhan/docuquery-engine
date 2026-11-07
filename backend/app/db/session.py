import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger
from app.db.models import Base

# Ensure parent directory for local db exists
os.makedirs("./data", exist_ok=True)

# Normalize SQLite URL if it still has async prefix
db_url = settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "")

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
