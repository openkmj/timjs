"""
S3 utility functions for media upload/download
"""

import os
from enum import Enum

import boto3
from nanoid import generate

from app.config import get_settings

settings = get_settings()


class MediaType(str, Enum):
    ORIGINAL = "media"
    THUMBNAIL = "media/thumb"
    PROFILE = "profile"


class S3Client:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )

    def generate_presigned_post(
        self,
        file_name: str,
        content_type: str,
        event_s3_key: str,
        media_type: MediaType = MediaType.ORIGINAL,
        expiration: int = 3600,
    ) -> dict | None:
        """
        Generate a presigned POST URL for uploading a file directly to S3
        Files are uploaded with public-read ACL for direct access
        Key format: media/event_s3_key/unique_id.ext
        """

        ext = os.path.splitext(file_name)[1]
        unique_id = generate(size=21)
        key = f"{media_type.value}/{event_s3_key}/{unique_id}{ext}"

        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=settings.s3_bucket_name,
                Key=key,
                Fields={
                    "acl": "public-read",
                    "Content-Type": content_type,
                },
                Conditions=[
                    {"acl": "public-read"},
                    {"Content-Type": content_type},
                    ["content-length-range", 1, 2147483648],  # Max 2GB
                ],
                ExpiresIn=expiration,
            )
            return {
                "url": response["url"],
                "fields": response["fields"],
                "key": key,
            }
        except Exception:
            return None

    def get_file_metadata(self, key: str) -> dict | None:
        try:
            response = self.s3_client.head_object(
                Bucket=settings.s3_bucket_name, Key=key
            )
            return {
                "size": response["ContentLength"],
                "content_type": response["ContentType"],
            }
        except Exception:
            return None

    def delete_file(self, key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=key)
            return True
        except Exception:
            return False


s3_client = S3Client()
