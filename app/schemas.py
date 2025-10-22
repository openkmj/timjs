from datetime import datetime

from pydantic import BaseModel, ConfigDict


# Event schemas
class EventBase(BaseModel):
    title: str
    description: str | None = None
    date: datetime
    location: str | None = None
    tags: list[str] | None = []


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    date: datetime | None = None
    location: str | None = None
    tags: list[str] | None = None


class EventResponse(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    thumbnails: list[str] = []


# Media schemas
class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MediaListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    user: UserSummary
    url: str
    thumb_url: str
    file_type: str
    file_size: int | None
    file_metadata: dict | None = None
    created_at: datetime


class MediaFeedResponse(BaseModel):
    items: list[MediaListItem]
    cursor: int | None = None
    has_more: bool


class PresignedUploadRequest(BaseModel):
    file_name: str
    content_type: str
    event_id: int


class PresignedUrlData(BaseModel):
    url: str
    fields: dict
    key: str


class PresignedUploadResponse(BaseModel):
    original: PresignedUrlData
    thumbnail: PresignedUrlData


class MediaUploadItem(BaseModel):
    s3_key: str
    thumb_s3_key: str
    event_id: int
    file_metadata: dict | None = None


class ConfirmUploadListRequest(BaseModel):
    media_list: list[MediaUploadItem]


# User schemas
class FriendSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    profile_img: str | None = None


class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    profile_img: str | None = None
    friends: list[FriendSummary] = []
    team_name: str
    storage_used: int
    storage_limit: int


class UpdatePushTokenRequest(BaseModel):
    expo_push_token: str


class ProfileImagePresignedRequest(BaseModel):
    file_name: str
    content_type: str


class UpdateProfileImageRequest(BaseModel):
    url: str
