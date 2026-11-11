from __future__ import annotations

from datetime import date, datetime, time, timezone
from math import ceil

from sqlalchemy import Select, distinct, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Meeting, MeetingParticipant, MeetingTag, Participant
from app.schemas.entities import (
    MeetingDetailResponse,
    MeetingLibraryItemResponse,
    MeetingListResponse,
    ParticipantResponse,
    TagResponse,
)


def list_meetings(
    session: Session,
    *,
    search: str | None,
    start_date: date | None,
    end_date: date | None,
    sort: str,
    page: int,
    page_size: int,
) -> MeetingListResponse:
    statement = _filtered_statement(search, start_date, end_date)
    total = session.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
    order_column = Meeting.meeting_date.desc() if sort == "newest" else Meeting.meeting_date.asc()
    meetings = session.scalars(
        statement.options(*_meeting_load_options())
        .order_by(order_column, Meeting.id.desc() if sort == "newest" else Meeting.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    return MeetingListResponse(
        items=[_library_response(meeting) for meeting in meetings],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


def get_meeting(session: Session, meeting_id: int) -> MeetingDetailResponse | None:
    meeting = session.scalar(
        select(Meeting).where(Meeting.id == meeting_id).options(*_meeting_load_options())
    )
    if meeting is None:
        return None
    item = _library_response(meeting)
    return MeetingDetailResponse(
        **item.model_dump(),
        recording_url=meeting.recording_url,
        recording_type=meeting.recording_type,
        source=meeting.source,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )


def _filtered_statement(
    search: str | None, start_date: date | None, end_date: date | None
) -> Select[tuple[Meeting]]:
    statement = select(Meeting)
    if search:
        query = f"%{search.strip().lower()}%"
        statement = statement.outerjoin(MeetingParticipant).outerjoin(Participant).where(
            or_(
                func.lower(Meeting.title).like(query),
                func.lower(Participant.name).like(query),
            )
        ).distinct()
    if start_date:
        statement = statement.where(
            Meeting.meeting_date >= datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        )
    if end_date:
        statement = statement.where(
            Meeting.meeting_date <= datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        )
    return statement


def _meeting_load_options() -> tuple[object, ...]:
    return (
        selectinload(Meeting.participant_links).selectinload(MeetingParticipant.participant),
        selectinload(Meeting.tag_links).selectinload(MeetingTag.tag),
        selectinload(Meeting.summary),
    )


def _library_response(meeting: Meeting) -> MeetingLibraryItemResponse:
    participants = [
        ParticipantResponse.model_validate(link.participant)
        for link in meeting.participant_links
    ]
    tags = [TagResponse.model_validate(link.tag) for link in meeting.tag_links]
    summary_preview = _summary_preview(meeting.summary.overview) if meeting.summary else None
    return MeetingLibraryItemResponse(
        id=meeting.id,
        title=meeting.title,
        description=meeting.description,
        meeting_date=meeting.meeting_date,
        duration_seconds=meeting.duration_seconds,
        participants=participants,
        participant_count=len(participants),
        tags=tags,
        summary_preview=summary_preview,
    )


def _summary_preview(overview: str, limit: int = 220) -> str:
    if len(overview) <= limit:
        return overview
    return f"{overview[: limit - 1].rstrip()}…"
