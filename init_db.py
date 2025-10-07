"""
Database initialization script
"""

from sqlalchemy import create_engine

from app.config import get_settings
from app.db.models import Base

settings = get_settings()


def init_database():
    """Initialize database tables only"""

    # Create engine
    engine = create_engine(
        settings.database_url, connect_args={"check_same_thread": False}
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


if __name__ == "__main__":
    init_database()
