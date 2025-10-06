from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.connection import SessionLocal


def _get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBContext = Annotated[Session, Depends(_get_db)]
