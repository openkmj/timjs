"""
SQLAlchemy models for the database
"""

from nanoid import generate
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False)
    expo_push_token = Column(String(255), nullable=True)

    media = relationship("Media", back_populates="user")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    s3_key = Column(String(21), unique=True, default=generate)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=True)
    tags = Column(Text, nullable=True)  # sepreated by ","

    media = relationship("Media", back_populates="event")


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    url = Column(Text, nullable=False)
    thumb_url = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_metadata = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)

    event = relationship("Event", back_populates="media")
    user = relationship("User", back_populates="media")
