from datetime import date, datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ParticipantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=320)
    avatar_url: str | None = Field(default=None, max_length=2048)


class ParticipantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=320)
    avatar_url: str | None = Field(default=None, max_length=2048)


class ParticipantResponse(ORMResponse):
    id: int
    name: str
    email: str | None
    avatar_url: str | None


class MeetingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    meeting_date: datetime
    duration_seconds: int = Field(ge=0)
    recording_url: str | None = Field(default=None, max_length=2048)
    recording_type: str | None = Field(default=None, max_length=50)
    source: str = Field(min_length=1, max_length=100)

    @field_validator("meeting_date")
    @classmethod
    def normalise_meeting_date(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("meeting_date must be timezone-aware")
        return value.astimezone(timezone.utc)


class MeetingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    meeting_date: datetime | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    recording_url: str | None = Field(default=None, max_length=2048)
    recording_type: str | None = Field(default=None, max_length=50)
    source: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("meeting_date")
    @classmethod
    def normalise_meeting_date(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("meeting_date must be timezone-aware")
        return value.astimezone(timezone.utc)


class MeetingResponse(ORMResponse):
    id: int
    title: str
    description: str
    meeting_date: datetime
    duration_seconds: int
    recording_url: str | None
    recording_type: str | None
    source: str
    created_at: datetime
    updated_at: datetime


class MeetingParticipantCreate(BaseModel):
    participant_id: int
    role: str | None = Field(default=None, max_length=100)


class MeetingParticipantUpdate(BaseModel):
    role: str | None = Field(default=None, max_length=100)


class MeetingParticipantResponse(ORMResponse):
    meeting_id: int
    participant_id: int
    role: str | None


class TranscriptSegmentCreate(BaseModel):
    participant_id: int | None = None
    start_time_ms: int = Field(ge=0)
    end_time_ms: int = Field(ge=0)
    text: str = Field(min_length=1)
    sequence_number: int = Field(ge=0)


class TranscriptSegmentUpdate(BaseModel):
    participant_id: int | None = None
    start_time_ms: int | None = Field(default=None, ge=0)
    end_time_ms: int | None = Field(default=None, ge=0)
    text: str | None = Field(default=None, min_length=1)
    sequence_number: int | None = Field(default=None, ge=0)


class TranscriptSegmentResponse(ORMResponse):
    id: int
    meeting_id: int
    participant_id: int | None
    start_time_ms: int
    end_time_ms: int
    text: str
    sequence_number: int
    created_at: datetime


class MeetingSummaryCreate(BaseModel):
    overview: str = Field(min_length=1)
    key_points: list[dict[str, Any]] = Field(default_factory=list)
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    generated_by: str = Field(min_length=1, max_length=100)


class MeetingSummaryUpdate(BaseModel):
    overview: str | None = Field(default=None, min_length=1)
    key_points: list[dict[str, Any]] | None = None
    decisions: list[dict[str, Any]] | None = None
    generated_by: str | None = Field(default=None, min_length=1, max_length=100)


class MeetingSummaryResponse(ORMResponse):
    id: int
    meeting_id: int
    overview: str
    key_points: list[dict[str, Any]]
    decisions: list[dict[str, Any]]
    generated_by: str
    created_at: datetime
    updated_at: datetime


class ActionItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = ""
    assignee_id: int | None = None
    due_date: date | None = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    status: str = Field(default="open", pattern="^(open|in_progress|completed|cancelled)$")


class ActionItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    assignee_id: int | None = None
    due_date: date | None = None
    priority: str | None = Field(default=None, pattern="^(low|medium|high|urgent)$")
    status: str | None = Field(default=None, pattern="^(open|in_progress|completed|cancelled)$")


class ActionItemResponse(ORMResponse):
    id: int
    meeting_id: int
    title: str
    description: str
    assignee_id: int | None
    due_date: date | None
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime


class ChapterCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    start_time_ms: int = Field(ge=0)
    end_time_ms: int = Field(ge=0)
    sequence_number: int = Field(ge=0)


class ChapterUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    start_time_ms: int | None = Field(default=None, ge=0)
    end_time_ms: int | None = Field(default=None, ge=0)
    sequence_number: int | None = Field(default=None, ge=0)


class ChapterResponse(ORMResponse):
    id: int
    meeting_id: int
    title: str
    description: str
    start_time_ms: int
    end_time_ms: int
    sequence_number: int


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(min_length=1, max_length=20)


class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, min_length=1, max_length=20)


class TagResponse(ORMResponse):
    id: int
    name: str
    color: str


class MeetingTagCreate(BaseModel):
    tag_id: int


class MeetingTagResponse(ORMResponse):
    meeting_id: int
    tag_id: int


class MeetingLibraryItemResponse(ORMResponse):
    id: int
    title: str
    description: str
    meeting_date: datetime
    duration_seconds: int
    participants: list[ParticipantResponse]
    participant_count: int
    tags: list[TagResponse]
    summary_preview: str | None


class MeetingDetailResponse(MeetingLibraryItemResponse):
    recording_url: str | None
    recording_type: str | None
    source: str
    created_at: datetime
    updated_at: datetime


class PaginationMetadata(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


class MeetingListResponse(BaseModel):
    items: list[MeetingLibraryItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
