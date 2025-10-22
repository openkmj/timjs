from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    database_url: str = "sqlite:////data/timjs.db"

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-northeast-2"
    s3_bucket_name: str = ""

    admin_username: str = "admin"
    admin_password: str = ""
    admin_secret_key: str = ""


@lru_cache
def get_settings():
    return Settings()
