from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.entities import (
    ActionItemResponse,
    ChapterResponse,
    MeetingLibraryItemResponse,
    MeetingSummaryResponse,
    ParticipantResponse,
    TagResponse,
)


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)


class NoteUpdate(NoteCreate):
    pass


class NoteResponse(ORMResponse):
    id: int
    meeting_id: int
    content: str
    created_at: datetime
    updated_at: datetime


class TranscriptSegmentDetailResponse(ORMResponse):
    id: int
    meeting_id: int
    participant_id: int | None
    start_time_ms: int
    end_time_ms: int
    text: str
    sequence_number: int
    participant: ParticipantResponse | None = None


class WorkspaceMeetingResponse(MeetingLibraryItemResponse):
    recording_url: str | None
    recording_type: str | None
    source: str
    created_at: datetime
    updated_at: datetime
    summary: MeetingSummaryResponse | None = None
    transcript_segments: list[TranscriptSegmentDetailResponse] = Field(default_factory=list)
    action_items: list[ActionItemResponse] = Field(default_factory=list)
    chapters: list[ChapterResponse] = Field(default_factory=list)
    notes: list[NoteResponse] = Field(default_factory=list)


class ActionItemPayload(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=20_000)
    assignee_id: int | None = None
    due_date: date | None = None
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    status: Literal["open", "in_progress", "completed", "cancelled"] = "open"


class ActionItemPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=20_000)
    assignee_id: int | None = None
    due_date: date | None = None
    priority: Literal["low", "medium", "high", "urgent"] | None = None
    status: Literal["open", "in_progress", "completed", "cancelled"] | None = None


class MeetingPayload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=20_000)
    meeting_date: datetime
    duration_seconds: int = Field(default=0, ge=0)
    participant_ids: list[int] = Field(default_factory=list)
    tag_names: list[str] = Field(default_factory=list)
    recording_url: str | None = Field(default=None, max_length=2048)
    recording_type: str | None = Field(default=None, max_length=50)
    source: str = Field(default="manual", min_length=1, max_length=100)

    @field_validator("meeting_date")
    @classmethod
    def aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("meeting_date must be timezone-aware")
        return value


class MeetingPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=20_000)
    meeting_date: datetime | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    participant_ids: list[int] | None = None
    tag_names: list[str] | None = None
    recording_url: str | None = Field(default=None, max_length=2048)
    recording_type: str | None = Field(default=None, max_length=50)
    source: str | None = Field(default=None, min_length=1, max_length=100)


class SummaryGenerationResponse(ORMResponse):
    id: int
    meeting_id: int
    overview: str
    key_points: list[dict[str, Any]]
    decisions: list[dict[str, Any]]
    generated_by: str
    created_at: datetime
    updated_at: datetime


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2_000)


class AskResponse(BaseModel):
    answer: str
    provider: str


class SearchResult(BaseModel):
    meeting: MeetingLibraryItemResponse
    match_type: Literal["meeting", "participant", "tag", "transcript"]
    snippet: str | None = None
    timestamp_ms: int | None = None


class SearchResponse(BaseModel):
    items: list[SearchResult]
