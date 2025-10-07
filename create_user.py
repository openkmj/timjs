"""
Create a new user with API key
"""

import argparse
import secrets
import string

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db.models import User

settings = get_settings()


def generate_api_key():
    """Generate a secure API key"""
    alphabet = string.ascii_letters + string.digits
    return "sk-" + "".join(secrets.choice(alphabet) for _ in range(32))


def create_user(name: str):
    """Create a new user with the given name"""

    # Create engine
    engine = create_engine(
        settings.database_url, connect_args={"check_same_thread": False}
    )

    session_local = sessionmaker(bind=engine)
    db = session_local()

    try:
        api_key = generate_api_key()
        user = User(name=name, api_key=api_key)
        db.add(user)
        db.commit()
        db.refresh(user)

        print("User created successfully")
        print(f"ID: {user.id}")
        print(f"Name: {user.name}")
        print(f"API Key: {api_key}")
        print("IMPORTANT: Save this API key securely. It won't be shown again!")

    except Exception as e:
        print(f"L Error creating user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new user")
    parser.add_argument("name", type=str, help="User name")
    args = parser.parse_args()

    create_user(args.name)
