"""
Events API 엔드포인트 테스트
"""

from unittest.mock import patch

import pytest


@pytest.mark.api
class TestEventsAPI:
    """Events API 테스트"""

    def test_get_events_success(self, client, sample_team, sample_user, sample_event):
        """이벤트 목록 조회 성공"""
        response = client.get(
            "/api/events",
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Event"
        assert data[0]["location"] == "Test Location"
        assert data[0]["tags"] == ["test", "event"]

    def test_get_events_unauthorized(self, client):
        """인증 없이 이벤트 조회 시 실패"""
        response = client.get("/api/events")
        assert response.status_code in [401, 403, 422]

    @patch("app.routers.events.send_push_notification")
    def test_create_event_success(
        self, mock_push, client, sample_team, sample_user, test_db
    ):
        """이벤트 생성 성공"""
        event_data = {
            "title": "New Event",
            "description": "New Description",
            "date": "2025-10-23T15:00:00",
            "location": "New Location",
            "tags": ["new", "test"],
        }
        response = client.post(
            "/api/events",
            json=event_data,
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 204

        # 푸시 알림이 호출되었는지 확인
        assert mock_push.called

        # DB에서 이벤트 조회
        from app.db.models import Event

        event = test_db.query(Event).filter_by(title="New Event").first()
        assert event is not None
        assert event.description == "New Description"

    def test_create_event_missing_fields(self, client, sample_user):
        """필수 필드 누락 시 이벤트 생성 실패"""
        event_data = {
            "title": "Incomplete Event",
            # date 필드 누락
        }
        response = client.post(
            "/api/events",
            json=event_data,
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 422

    def test_delete_event_success(self, client, sample_user, sample_event):
        """이벤트 삭제 성공 (미디어 없음)"""
        response = client.delete(
            f"/api/events/{sample_event.id}",
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 204

    def test_delete_event_with_media(
        self, client, sample_user, sample_event, sample_media
    ):
        """미디어가 연결된 이벤트 삭제 시 실패"""
        response = client.delete(
            f"/api/events/{sample_event.id}",
            headers={"Authorization": f"Bearer {sample_user.api_key}"},
        )
        assert response.status_code == 400
        assert "Cannot delete event with connected media" in response.json()["detail"]
