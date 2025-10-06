from datetime import datetime

from pydantic import BaseModel


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
    id: int

    class Config:
        from_attributes = True


# Media schemas
class UserSummary(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MediaListItem(BaseModel):
    id: int
    event_id: int
    user: UserSummary
    url: str
    thumb_url: str
    file_type: str
    file_size: int | None
    file_metadata: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class MediaFeedResponse(BaseModel):
    items: list[MediaListItem]
    cursor: str | None = None
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
    url: str
    thumb_url: str
    file_type: str
    event_id: int
    file_size: int
    file_metadata: dict | None = None


class ConfirmUploadListRequest(BaseModel):
    media_list: list[MediaUploadItem]


# User schemas
class UserMeResponse(BaseModel):
    id: int
    name: str
    profile_img: str | None = None

    class Config:
        from_attributes = True


class UpdatePushTokenRequest(BaseModel):
    expo_push_token: str
