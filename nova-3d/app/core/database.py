"""
NOVA 3D - Database Engine & Session Management
Provides SQLAlchemy Base, engine, sessionmaker, and initialization routines.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from app.config import DATABASE_URL
from app.core.logging import logger

# SQLite connect args to allow multithreaded access
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base()

def get_db():
    """Dependency for FastAPI route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Creates all registered database tables."""
    import app.models # Ensure all models are registered
    Base.metadata.create_all(bind=engine)
    logger.info("Initialized database schema successfully.")
