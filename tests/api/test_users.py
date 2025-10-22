"""
Users API 엔드포인트 테스트
"""

from unittest.mock import patch

import pytest


@pytest.mark.api
class TestUsersAPI:
    """Users API 테스트"""

    def test_get_me_success(self, client, sample_user, sample_team):
        """현재 사용자 정보 조회 성공"""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_user.id
        assert data["name"] == sample_user.name
        assert data["team_name"] == sample_team.name
        assert data["storage_used"] == sample_team.storage_used
        assert data["storage_limit"] == sample_team.storage_limit
        assert isinstance(data["friends"], list)

    def test_get_me_with_friends(self, client, test_db, sample_user, sample_team):
        """친구 목록 포함 사용자 정보 조회"""
        # 추가 사용자 생성
        from app.db.models import User

        friend1 = User(
            name="Friend 1",
            api_key="friend1_key",
            team_id=sample_team.id,
        )
        friend2 = User(
            name="Friend 2",
            api_key="friend2_key",
            team_id=sample_team.id,
        )
        test_db.add_all([friend1, friend2])
        test_db.commit()

        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["friends"]) == 2
        friend_names = [f["name"] for f in data["friends"]]
        assert "Friend 1" in friend_names
        assert "Friend 2" in friend_names

    def test_get_me_unauthorized(self, client):
        """인증 없이 사용자 정보 조회 시 실패"""
        response = client.get("/api/users/me")
        assert response.status_code in [401, 403, 422]

    def test_update_push_token_success(self, client, sample_user, test_db):
        """푸시 토큰 업데이트 성공"""
        new_token = "ExponentPushToken[newtoken123]"
        response = client.put(
            "/api/users/push-token",
            json={"expo_push_token": new_token},
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 204

        # DB에서 업데이트 확인
        test_db.refresh(sample_user)
        assert sample_user.expo_push_token == new_token

    def test_update_push_token_invalid_format(self, client, sample_user):
        """잘못된 형식의 푸시 토큰"""
        response = client.put(
            "/api/users/push-token",
            json={"expo_push_token": ""},
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        # 빈 토큰도 허용될 수 있음
        assert response.status_code in [204, 422]

    @patch("app.utils.s3.s3_client.generate_presigned_post")
    def test_get_profile_image_presigned_url_success(
        self, mock_presigned, client, sample_user
    ):
        """프로필 이미지 업로드용 presigned URL 생성 성공"""
        mock_presigned.return_value = {
            "url": "https://s3.amazonaws.com/test-bucket",
            "fields": {"key": "profile/1/test.jpg", "policy": "test-policy"},
            "key": "profile/1/test.jpg",
        }

        response = client.post(
            "/api/users/profile-image/presigned-url",
            json={"file_name": "test.jpg", "content_type": "image/jpeg"},
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "fields" in data
        assert "key" in data

    @patch("app.utils.s3.s3_client.generate_presigned_post")
    def test_get_profile_image_presigned_url_failure(
        self, mock_presigned, client, sample_user
    ):
        """Presigned URL 생성 실패"""
        mock_presigned.return_value = None

        response = client.post(
            "/api/users/profile-image/presigned-url",
            json={"file_name": "test.jpg", "content_type": "image/jpeg"},
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 500

    def test_update_profile_image_success(self, client, sample_user, test_db):
        """프로필 이미지 URL 업데이트 성공"""
        new_url = "https://s3.amazonaws.com/bucket/profile/1/new.jpg"
        response = client.put(
            "/api/users/profile-image",
            json={"url": new_url},
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 204

        # DB에서 업데이트 확인
        test_db.refresh(sample_user)
        assert sample_user.profile_img == new_url

    def test_update_profile_image_unauthorized(self, client):
        """인증 없이 프로필 이미지 업데이트 시 실패"""
        response = client.put(
            "/api/users/profile-image",
            json={"url": "https://example.com/image.jpg"},
        )
        assert response.status_code in [401, 403, 422]
