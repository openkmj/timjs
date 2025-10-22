"""
Media API 엔드포인트 테스트
"""

from datetime import datetime
from unittest.mock import patch

import pytest


@pytest.mark.api
class TestMediaAPI:
    """Media API 테스트"""

    @patch("app.utils.s3.s3_client.generate_presigned_post")
    def test_get_presigned_upload_url_success(
        self, mock_presigned, client, sample_user, sample_event
    ):
        """미디어 업로드용 presigned URL 생성 성공"""
        mock_presigned.side_effect = [
            {  # original
                "url": "https://s3.amazonaws.com/test-bucket",
                "fields": {"key": "original/test.jpg"},
                "key": "original/test.jpg",
            },
            {  # thumbnail
                "url": "https://s3.amazonaws.com/test-bucket",
                "fields": {"key": "thumb/test.jpg"},
                "key": "thumb/test.jpg",
            },
        ]

        response = client.post(
            "/api/media/presigned-url",
            json={
                "event_id": sample_event.id,
                "file_name": "test.jpg",
                "content_type": "image/jpeg",
            },
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "original" in data
        assert "thumbnail" in data
        assert data["original"]["url"] == "https://s3.amazonaws.com/test-bucket"

    @patch("app.utils.s3.s3_client.generate_presigned_post")
    def test_get_presigned_upload_url_event_not_found(
        self, mock_presigned, client, sample_user
    ):
        """존재하지 않는 이벤트에 대한 presigned URL 요청 시 실패"""
        response = client.post(
            "/api/media/presigned-url",
            json={
                "event_id": 99999,
                "file_name": "test.jpg",
                "content_type": "image/jpeg",
            },
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 404

    @patch("app.utils.s3.s3_client.generate_presigned_post")
    def test_get_presigned_upload_url_storage_limit_exceeded(
        self, mock_presigned, client, sample_user, sample_event, test_db
    ):
        """스토리지 한도 초과 시 presigned URL 요청 실패"""
        # 팀의 스토리지를 한도까지 채움
        from app.db.models import Team

        team = test_db.query(Team).filter_by(id=sample_user.team_id).first()
        team.storage_used = team.storage_limit
        test_db.commit()

        response = client.post(
            "/api/media/presigned-url",
            json={
                "event_id": sample_event.id,
                "file_name": "test.jpg",
                "content_type": "image/jpeg",
            },
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 403

    @patch("app.utils.s3.s3_client.get_file_metadata")
    @patch("app.routers.media.send_push_notification")
    def test_create_media_success(
        self, mock_push, mock_metadata, client, sample_user, sample_event, test_db
    ):
        """미디어 생성 성공"""
        mock_metadata.return_value = {
            "size": 1024,
            "content_type": "image/jpeg",
        }

        response = client.post(
            "/api/media",
            json={
                "media_list": [
                    {
                        "event_id": sample_event.id,
                        "s3_key": "original/test.jpg",
                        "thumb_s3_key": "thumb/test.jpg",
                        "file_metadata": {"width": 1920, "height": 1080},
                    }
                ]
            },
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 204

        # DB에서 미디어 조회
        from app.db.models import Media

        media = test_db.query(Media).filter_by(event_id=sample_event.id).first()
        assert media is not None
        assert media.file_type == "image/jpeg"
        assert media.file_size == 1024

        # 푸시 알림이 호출되었는지 확인
        assert mock_push.called

    @patch("app.utils.s3.s3_client.get_file_metadata")
    def test_create_media_file_not_found(
        self, mock_metadata, client, sample_user, sample_event
    ):
        """S3에 파일이 없는 경우 미디어 생성 실패"""
        mock_metadata.return_value = None

        response = client.post(
            "/api/media",
            json={
                "media_list": [
                    {
                        "event_id": sample_event.id,
                        "s3_key": "nonexistent.jpg",
                        "thumb_s3_key": "nonexistent_thumb.jpg",
                    }
                ]
            },
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 400

    @patch("app.utils.s3.s3_client.get_file_metadata")
    def test_create_media_storage_limit_exceeded(
        self, mock_metadata, client, sample_user, sample_event, test_db
    ):
        """스토리지 한도 초과 시 미디어 생성 실패"""
        # 큰 파일 크기로 설정
        mock_metadata.return_value = {
            "size": 10 * 1024 * 1024 * 1024,  # 10GB
            "content_type": "image/jpeg",
        }

        response = client.post(
            "/api/media",
            json={
                "media_list": [
                    {
                        "event_id": sample_event.id,
                        "s3_key": "original/huge.jpg",
                        "thumb_s3_key": "thumb/huge.jpg",
                    }
                ]
            },
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 403

    def test_get_media_feed_success(self, client, sample_user, sample_media):
        """미디어 피드 조회 성공"""
        response = client.get(
            "/api/media",
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "cursor" in data
        assert "has_more" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == sample_media.id

    def test_get_media_feed_with_cursor(
        self, client, sample_user, test_db, sample_event
    ):
        """커서 기반 페이지네이션"""
        # 여러 미디어 생성
        from app.db.models import Media

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

        response = client.get(
            "/api/media",
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5

    def test_delete_media_success(self, client, sample_user, sample_media):
        """미디어 삭제 성공"""
        response = client.delete(
            f"/api/media/{sample_media.id}",
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 204

    def test_delete_media_not_found(self, client, sample_user):
        """존재하지 않는 미디어 삭제 시 실패"""
        response = client.delete(
            "/api/media/99999",
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 404

    def test_delete_media_unauthorized(
        self, client, test_db, sample_team, sample_event, sample_media
    ):
        """다른 사용자의 미디어 삭제 시 실패"""
        # 다른 사용자 생성
        from app.db.models import User

        other_user = User(
            name="Other User",
            api_key="other_api_key",
            team_id=sample_team.id,
        )
        test_db.add(other_user)
        test_db.commit()

        response = client.delete(
            f"/api/media/{sample_media.id}",
            headers={"Authorization": f"Bearer {other_user.api_key}"},
        )
        assert response.status_code == 403
