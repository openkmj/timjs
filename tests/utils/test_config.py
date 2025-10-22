"""
Config 유틸리티 테스트
"""

from unittest.mock import patch

import pytest

from app.utils.config import Settings, get_settings


@pytest.mark.unit
class TestSettings:
    """Settings 설정 테스트"""

    def test_settings_default_values(self):
        """기본값 테스트"""
        settings = Settings()
        # database_url은 환경에 따라 다를 수 있으므로 sqlite인지만 확인
        assert "sqlite" in settings.database_url
        assert settings.aws_region == "ap-northeast-2"
        assert settings.admin_username == "admin"

    def test_settings_with_env_override(self):
        """환경 변수 오버라이드 테스트"""
        with patch.dict(
            "os.environ",
            {
                "DATABASE_URL": "sqlite:///test.db",
                "AWS_REGION": "us-east-1",
                "S3_BUCKET_NAME": "test-bucket",
            },
        ):
            # LRU 캐시 초기화
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.database_url == "sqlite:///test.db"
            assert settings.aws_region == "us-east-1"
            assert settings.s3_bucket_name == "test-bucket"

    def test_get_settings_caching(self):
        """get_settings가 캐싱되는지 테스트"""
        get_settings.cache_clear()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2  # 같은 객체
