from __future__ import annotations

from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import (
    ActionItem,
    Meeting,
    MeetingNote,
    MeetingParticipant,
    MeetingSummary,
    MeetingTag,
    Participant,
    Tag,
    TranscriptSegment,
)
from app.schemas.entities import ActionItemResponse, ChapterResponse, MeetingSummaryResponse, ParticipantResponse, TagResponse
from app.schemas.workspace import (
    ActionItemPatch, ActionItemPayload, MeetingPatch, MeetingPayload, NoteCreate, NoteResponse,
    NoteUpdate, SearchResponse, SearchResult, TranscriptSegmentDetailResponse, WorkspaceMeetingResponse,
)
from app.services.meetings import _library_response, _meeting_load_options


def meeting_options() -> tuple[object, ...]:
    return (*_meeting_load_options(), selectinload(Meeting.transcript_segments).selectinload(TranscriptSegment.participant),
            selectinload(Meeting.action_items).selectinload(ActionItem.assignee), selectinload(Meeting.chapters), selectinload(Meeting.notes))


def get_workspace_meeting(session: Session, meeting_id: int) -> WorkspaceMeetingResponse | None:
    meeting = session.scalar(select(Meeting).where(Meeting.id == meeting_id).options(*meeting_options()))
    return serialize_meeting(meeting) if meeting else None


def serialize_meeting(meeting: Meeting) -> WorkspaceMeetingResponse:
    library = _library_response(meeting)
    return WorkspaceMeetingResponse(
        **library.model_dump(), recording_url=meeting.recording_url, recording_type=meeting.recording_type,
        source=meeting.source, created_at=meeting.created_at, updated_at=meeting.updated_at,
        summary=MeetingSummaryResponse.model_validate(meeting.summary) if meeting.summary else None,
        transcript_segments=[TranscriptSegmentDetailResponse(
            id=item.id, meeting_id=item.meeting_id, participant_id=item.participant_id,
            start_time_ms=item.start_time_ms, end_time_ms=item.end_time_ms, text=item.text,
            sequence_number=item.sequence_number,
            participant=ParticipantResponse.model_validate(item.participant) if item.participant else None,
        ) for item in meeting.transcript_segments],
        action_items=[ActionItemResponse.model_validate(item) for item in meeting.action_items],
        chapters=[ChapterResponse.model_validate(item) for item in meeting.chapters],
        notes=[NoteResponse.model_validate(item) for item in meeting.notes],
    )


def _participants(session: Session, ids: list[int]) -> list[Participant]:
    if not ids:
        return []
    found = session.scalars(select(Participant).where(Participant.id.in_(set(ids)))).all()
    if len(found) != len(set(ids)):
        raise ValueError("One or more participant IDs do not exist")
    return found


def _tags(session: Session, names: list[str]) -> list[Tag]:
    normalized = [name.strip() for name in names if name.strip()]
    if len(normalized) != len(set(value.lower() for value in normalized)):
        raise ValueError("Tag names must be unique")
    tags: list[Tag] = []
    for name in normalized:
        tag = session.scalar(select(Tag).where(func.lower(Tag.name) == name.lower()))
        if not tag:
            tag = Tag(name=name, color="#6366f1")
            session.add(tag)
            session.flush()
        tags.append(tag)
    return tags


def create_meeting(session: Session, payload: MeetingPayload) -> WorkspaceMeetingResponse:
    meeting = Meeting(title=payload.title, description=payload.description, meeting_date=payload.meeting_date,
                      duration_seconds=payload.duration_seconds, recording_url=payload.recording_url,
                      recording_type=payload.recording_type, source=payload.source)
    session.add(meeting)
    session.flush()
    meeting.participant_links = [MeetingParticipant(participant=item) for item in _participants(session, payload.participant_ids)]
    meeting.tag_links = [MeetingTag(tag=item) for item in _tags(session, payload.tag_names)]
    _commit(session)
    return get_workspace_meeting(session, meeting.id)  # type: ignore[return-value]


def update_meeting(session: Session, meeting: Meeting, payload: MeetingPatch) -> WorkspaceMeetingResponse:
    values = payload.model_dump(exclude_unset=True)
    participant_ids = values.pop("participant_ids", None)
    tag_names = values.pop("tag_names", None)
    for key, value in values.items():
        setattr(meeting, key, value)
    if participant_ids is not None:
        meeting.participant_links = [MeetingParticipant(participant=item) for item in _participants(session, participant_ids)]
    if tag_names is not None:
        meeting.tag_links = [MeetingTag(tag=item) for item in _tags(session, tag_names)]
    _commit(session)
    return get_workspace_meeting(session, meeting.id)  # type: ignore[return-value]


def create_action(session: Session, meeting: Meeting, payload: ActionItemPayload) -> ActionItem:
    if payload.assignee_id and not session.get(Participant, payload.assignee_id):
        raise ValueError("Assignee does not exist")
    item = ActionItem(meeting=meeting, **payload.model_dump())
    session.add(item); _commit(session); return item


def update_action(session: Session, item: ActionItem, payload: ActionItemPatch) -> ActionItem:
    values = payload.model_dump(exclude_unset=True)
    if values.get("assignee_id") and not session.get(Participant, values["assignee_id"]):
        raise ValueError("Assignee does not exist")
    for key, value in values.items(): setattr(item, key, value)
    _commit(session); return item


def create_note(session: Session, meeting: Meeting, payload: NoteCreate) -> MeetingNote:
    note = MeetingNote(meeting=meeting, content=payload.content); session.add(note); _commit(session); return note


def update_note(session: Session, note: MeetingNote, payload: NoteUpdate) -> MeetingNote:
    note.content = payload.content; _commit(session); return note


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError("That change conflicts with existing data") from exc


def search_meetings(session: Session, query: str) -> SearchResponse:
    term = f"%{query.strip().lower()}%"
    statements = select(Meeting).outerjoin(MeetingParticipant).outerjoin(Participant).outerjoin(MeetingTag).outerjoin(Tag).where(or_(
        func.lower(Meeting.title).like(term), func.lower(Meeting.description).like(term), func.lower(Participant.name).like(term), func.lower(Tag.name).like(term)
    )).distinct().options(*_meeting_load_options())
    results: dict[int, SearchResult] = {}
    for meeting in session.scalars(statements).unique():
        results[meeting.id] = SearchResult(meeting=_library_response(meeting), match_type="meeting")
    transcript_rows = session.execute(select(TranscriptSegment, Meeting).join(Meeting).where(func.lower(TranscriptSegment.text).like(term)).options(*_meeting_load_options())).all()
    for segment, meeting in transcript_rows:
        results.setdefault(meeting.id, SearchResult(meeting=_library_response(meeting), match_type="transcript", snippet=segment.text[:240], timestamp_ms=segment.start_time_ms))
    return SearchResponse(items=list(results.values())[:30])


def transcript_context(meeting: Meeting) -> str:
    transcript = "\n".join(f"{segment.participant.name if segment.participant else 'Unidentified'}: {segment.text}" for segment in meeting.transcript_segments)
    actions = "\n".join(f"- {item.title} ({item.status})" for item in meeting.action_items)
    summary = meeting.summary.overview if meeting.summary else "No summary available."
    return f"Summary:\n{summary}\n\nAction items:\n{actions}\n\nTranscript:\n{transcript}"
