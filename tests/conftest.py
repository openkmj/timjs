"""
pytest fixtures for testing
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Event, Media, Team, User
from app.main import app


# 테스트용 인메모리 SQLite DB 엔진 생성
@pytest.fixture(scope="function")
def test_engine():
    """각 테스트마다 새로운 인메모리 DB 엔진 생성"""
    # StaticPool을 사용하여 같은 연결을 재사용
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # 같은 연결 재사용
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """테스트용 DB 세션 생성 (test_db와 client가 같은 엔진 사용)"""
    connection = test_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=connection
    )
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(test_engine, test_db):
    """FastAPI TestClient 생성 (test_db와 같은 엔진 공유)"""
    from app.middlewares.db import _get_db

    # DB 세션을 테스트용으로 오버라이드
    # test_db와 같은 세션을 반환하도록 수정
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # test_db fixture가 관리하므로 여기서는 close 하지 않음

    # DB dependency 오버라이드
    app.dependency_overrides[_get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# 테스트 데이터 픽스처
@pytest.fixture
def sample_team(test_db):
    """샘플 팀 데이터"""
    team = Team(
        name="Test Team",
        storage_limit=1048576,
        storage_used=0,
    )
    test_db.add(team)
    test_db.commit()
    test_db.refresh(team)
    return team


@pytest.fixture
def sample_user(test_db, sample_team):
    """샘플 사용자 데이터"""
    user = User(
        name="Test User",
        api_key="test_api_key_123",
        expo_push_token="ExponentPushToken[test123]",
        team_id=sample_team.id,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def sample_event(test_db, sample_team):
    """샘플 이벤트 데이터"""
    event = Event(
        title="Test Event",
        description="Test Description",
        date=datetime(2025, 10, 22, 10, 0, 0),
        location="Test Location",
        tags="test,event",
        team_id=sample_team.id,
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)
    return event


@pytest.fixture
def sample_media(test_db, sample_event, sample_user, sample_team):
    """샘플 미디어 데이터"""
    import math

    media = Media(
        event_id=sample_event.id,
        user_id=sample_user.id,
        url="https://test.s3.amazonaws.com/test.jpg",
        thumb_url="https://test.s3.amazonaws.com/test_thumb.jpg",
        file_type="image/jpeg",
        file_size=1024,
        created_at=datetime.now(),
    )
    test_db.add(media)

    # 스토리지 사용량 증가
    size_kb = math.ceil(media.file_size / 1024)
    sample_team.storage_used += size_kb

    test_db.commit()
    test_db.refresh(media)
    return media


@pytest.fixture
def auth_headers(sample_user):
    """인증 헤더"""
    return {"Authorization": f"Bearer {sample_user.api_key}"}
