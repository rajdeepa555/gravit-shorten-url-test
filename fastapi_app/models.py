"""
SQLAlchemy models for FastAPI URL shortener.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

DATABASE_URL = "sqlite:///./fastapi_shorten_url.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ShortenUrl(Base):
    """Model for storing shortened URL details."""
    __tablename__ = "shorten_url"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_url = Column(String(2048), nullable=False)
    short_code = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "original_url": self.original_url,
            "short_code": self.short_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


Base.metadata.create_all(bind=engine)
