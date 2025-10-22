"""
데이터베이스 쿼리 함수 테스트
"""

from datetime import datetime

import pytest

from app.db import query
from app.db.models import Event, Media, User


@pytest.mark.db
class TestEventQueries:
    """Event 관련 쿼리 테스트"""

    def test_list_events(self, test_db, sample_team, sample_event):
        """이벤트 목록 조회"""
        events = query.list_events(test_db, sample_team.id)
        assert len(events) == 1
        assert events[0].title == "Test Event"

    def test_list_events_with_thumbnails(
        self, test_db, sample_team, sample_event, sample_user
    ):
        """썸네일 포함 이벤트 목록 조회"""
        # 미디어 추가
        for i in range(5):
            media = Media(
                event_id=sample_event.id,
                user_id=sample_user.id,
                url=f"https://test.s3.amazonaws.com/test{i}.jpg",
                thumb_url=f"https://test.s3.amazonaws.com/test{i}_thumb.jpg",
                file_type="image/jpeg",
                file_size=1024,
                created_at=datetime.now(),
            )
            test_db.add(media)
        test_db.commit()

        events = query.list_events(test_db, sample_team.id)
        assert len(events) == 1
        assert hasattr(events[0], "thumbnails")
        assert len(events[0].thumbnails) == 3  # 최대 3개

    def test_get_event_success(self, test_db, sample_team, sample_event):
        """이벤트 ID로 조회 성공"""
        event = query.get_event(test_db, sample_event.id, sample_team.id)
        assert event is not None
        assert event.title == "Test Event"

    def test_get_event_not_found(self, test_db, sample_team):
        """존재하지 않는 이벤트 조회"""
        event = query.get_event(test_db, 99999, sample_team.id)
        assert event is None

    def test_get_event_wrong_team(self, test_db, sample_event):
        """다른 팀의 이벤트 조회 실패"""
        event = query.get_event(test_db, sample_event.id, 99999)
        assert event is None

    def test_create_event(self, test_db, sample_team):
        """이벤트 생성"""
        query.create_event(
            db=test_db,
            title="New Event",
            date=datetime(2025, 10, 25, 10, 0, 0),
            team_id=sample_team.id,
            description="New Description",
            location="New Location",
            tags=["new", "test"],
        )

        events = query.list_events(test_db, sample_team.id)
        assert len(events) == 1
        assert events[0].title == "New Event"
        assert events[0].tags == "new,test"

    def test_update_event(self, test_db, sample_event):
        """이벤트 수정"""
        query.update_event(
            db=test_db,
            event=sample_event,
            title="Updated Title",
            location="Updated Location",
        )

        test_db.refresh(sample_event)
        assert sample_event.title == "Updated Title"
        assert sample_event.location == "Updated Location"

    def test_delete_event(self, test_db, sample_event):
        """이벤트 삭제"""
        event_id = sample_event.id
        query.delete_event(test_db, sample_event)

        event = test_db.query(Event).filter(Event.id == event_id).first()
        assert event is None

    def test_has_media_true(self, test_db, sample_event, sample_media):
        """이벤트에 미디어가 있는 경우"""
        assert query.has_media(test_db, sample_event.id) is True

    def test_has_media_false(self, test_db, sample_event):
        """이벤트에 미디어가 없는 경우"""
        assert query.has_media(test_db, sample_event.id) is False


@pytest.mark.db
class TestMediaQueries:
    """Media 관련 쿼리 테스트"""

    def test_get_media_success(self, test_db, sample_media):
        """미디어 ID로 조회 성공"""
        media = query.get_media(test_db, sample_media.id)
        assert media is not None
        assert media.file_type == "image/jpeg"

    def test_get_media_not_found(self, test_db):
        """존재하지 않는 미디어 조회"""
        media = query.get_media(test_db, 99999)
        assert media is None

    def test_create_media_bulk(self, test_db, sample_event, sample_user, sample_team):
        """미디어 일괄 생성"""
        media_data_list = [
            {
                "event_id": sample_event.id,
                "url": "https://test.s3.amazonaws.com/test1.jpg",
                "thumb_url": "https://test.s3.amazonaws.com/test1_thumb.jpg",
                "file_type": "image/jpeg",
                "file_size": 2048,
                "created_at": datetime.now(),
            },
            {
                "event_id": sample_event.id,
                "url": "https://test.s3.amazonaws.com/test2.jpg",
                "thumb_url": "https://test.s3.amazonaws.com/test2_thumb.jpg",
                "file_type": "image/jpeg",
                "file_size": 4096,
                "created_at": datetime.now(),
            },
        ]

        initial_storage = sample_team.storage_used

        query.create_media_bulk(
            db=test_db,
            user_id=sample_user.id,
            media_data_list=media_data_list,
            team_id=sample_team.id,
        )

        media_list = (
            test_db.query(Media).filter(Media.event_id == sample_event.id).all()
        )
        assert len(media_list) == 2

        # 스토리지 사용량 증가 확인 (2048 + 4096 = 6144 bytes = 6 KB)
        test_db.refresh(sample_team)
        expected_increase = 6  # ceil(6144 / 1024)
        assert sample_team.storage_used == initial_storage + expected_increase

    def test_delete_media(self, test_db, sample_media, sample_team):
        """미디어 삭제 및 스토리지 감소 확인"""
        initial_storage = sample_team.storage_used
        media_id = sample_media.id

        query.delete_media(test_db, sample_media, sample_team.id)

        media = test_db.query(Media).filter(Media.id == media_id).first()
        assert media is None

        # 스토리지 사용량 감소 확인
        test_db.refresh(sample_team)
        expected_decrease = 1  # ceil(1024 / 1024)
        assert sample_team.storage_used == initial_storage - expected_decrease

    def test_get_media_feed(self, test_db, sample_event, sample_user, sample_team):
        """미디어 피드 조회"""
        # 여러 미디어 생성
        for i in range(10):
            media = Media(
                event_id=sample_event.id,
                user_id=sample_user.id,
                url=f"https://test.s3.amazonaws.com/test{i}.jpg",
                thumb_url=f"https://test.s3.amazonaws.com/test{i}_thumb.jpg",
                file_type="image/jpeg",
                file_size=1024,
                created_at=datetime.now(),
            )
            test_db.add(media)
        test_db.commit()

        media_list, next_cursor, has_more = query.get_media_feed(
            test_db, limit=5, team_id=sample_team.id
        )
        assert len(media_list) == 5
        assert has_more is True
        assert next_cursor is not None

    def test_get_media_feed_with_cursor(
        self, test_db, sample_event, sample_user, sample_team
    ):
        """커서 기반 페이지네이션"""
        # 미디어 생성
        for i in range(10):
            media = Media(
                event_id=sample_event.id,
                user_id=sample_user.id,
                url=f"https://test.s3.amazonaws.com/test{i}.jpg",
                thumb_url=f"https://test.s3.amazonaws.com/test{i}_thumb.jpg",
                file_type="image/jpeg",
                file_size=1024,
                created_at=datetime.now(),
            )
            test_db.add(media)
        test_db.commit()

        # 첫 페이지
        media_list_1, cursor, has_more = query.get_media_feed(
            test_db, limit=5, team_id=sample_team.id
        )
        assert len(media_list_1) == 5
        assert has_more is True

        # 두 번째 페이지
        media_list_2, cursor_2, has_more_2 = query.get_media_feed(
            test_db, limit=5, cursor=cursor, team_id=sample_team.id
        )
        assert len(media_list_2) == 5
        assert has_more_2 is False


@pytest.mark.db
class TestUserQueries:
    """User 관련 쿼리 테스트"""

    def test_get_user_by_api_key(self, test_db, sample_user):
        """API 키로 사용자 조회"""
        user = query.get_user(test_db, api_key=sample_user.api_key)
        assert user is not None
        assert user.name == "Test User"

    def test_get_user_by_id(self, test_db, sample_user):
        """사용자 ID로 조회"""
        user = query.get_user(test_db, user_id=sample_user.id)
        assert user is not None
        assert user.name == "Test User"

    def test_get_user_not_found(self, test_db):
        """존재하지 않는 사용자 조회"""
        user = query.get_user(test_db, api_key="nonexistent_key")
        assert user is None

    def test_get_user_no_params(self, test_db):
        """파라미터 없이 조회 시 에러"""
        with pytest.raises(ValueError):
            query.get_user(test_db)

    def test_list_users(self, test_db, sample_team, sample_user):
        """팀 사용자 목록 조회"""
        # 추가 사용자 생성
        user2 = User(
            name="User 2",
            api_key="user2_key",
            team_id=sample_team.id,
        )
        test_db.add(user2)
        test_db.commit()

        users = query.list_users(test_db, sample_team.id)
        assert len(users) == 2

    def test_update_user_expo_token(self, test_db, sample_user):
        """사용자 Expo 푸시 토큰 업데이트"""
        new_token = "ExponentPushToken[new123]"
        query.update_user(test_db, sample_user.id, expo_push_token=new_token)

        test_db.refresh(sample_user)
        assert sample_user.expo_push_token == new_token

    def test_update_user_profile_img(self, test_db, sample_user):
        """사용자 프로필 이미지 업데이트"""
        new_img = "https://example.com/profile.jpg"
        query.update_user(test_db, sample_user.id, profile_img=new_img)

        test_db.refresh(sample_user)
        assert sample_user.profile_img == new_img


@pytest.mark.db
class TestTeamQueries:
    """Team 관련 쿼리 테스트"""

    def test_get_team(self, test_db, sample_team):
        """팀 조회"""
        team = query.get_team(test_db, sample_team.id)
        assert team is not None
        assert team.name == "Test Team"
        assert team.storage_limit == 1048576

    def test_get_team_not_found(self, test_db):
        """존재하지 않는 팀 조회"""
        team = query.get_team(test_db, 99999)
        assert team is None
