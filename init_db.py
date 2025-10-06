"""
Database initialization script
"""

import secrets
import string
from pathlib import Path

from sqlalchemy import create_engine

from app.config import get_settings
from app.db.models import Base, User

settings = get_settings()


def generate_api_key():
    """Generate a secure API key"""
    alphabet = string.ascii_letters + string.digits
    return "sk-" + "".join(secrets.choice(alphabet) for _ in range(32))


def init_database():
    """Initialize database tables and create sample users"""

    # Create data directory if it doesn't exist
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)

    # Create engine
    engine = create_engine(
        settings.database_url, connect_args={"check_same_thread": False}
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

    # Create sample users
    from sqlalchemy.orm import sessionmaker

    session_local = sessionmaker(bind=engine)
    db = session_local()

    try:
        # Check if users already exist
        existing_users = db.query(User).count()

        if existing_users == 0:
            # Create sample users
            sample_users = [
                {"name": "김철수", "api_key": generate_api_key()},
                {"name": "이영희", "api_key": generate_api_key()},
                {"name": "박민수", "api_key": generate_api_key()},
                {"name": "정수진", "api_key": generate_api_key()},
                {"name": "홍길동", "api_key": generate_api_key()},
                {"name": "임하나", "api_key": generate_api_key()},
            ]

            for user_data in sample_users:
                user = User(**user_data)
                db.add(user)
                name = user_data["name"]
                api_key = user_data["api_key"]
                print(f"Created user: {name} with API key: {api_key}")

            db.commit()
            print("\n✅ Sample users created successfully")
            print(
                "\n⚠️  IMPORTANT: Save these API keys securely. "
                "They won't be shown again!"
            )
        else:
            print(
                f"ℹ️  Database already has {existing_users} users. "
                "Skipping user creation."
            )

    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
