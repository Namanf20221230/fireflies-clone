from __future__ import annotations

import io
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import ActionItem, Meeting, MeetingNote, MeetingSummary, Participant, TranscriptSegment
from app.schemas.entities import ActionItemResponse, ChapterResponse, MeetingSummaryResponse, TranscriptSegmentResponse
from app.schemas.workspace import (
    ActionItemPatch, ActionItemPayload, AskRequest, AskResponse, MeetingPatch, MeetingPayload, NoteCreate,
    NoteResponse, NoteUpdate, SearchResponse, SummaryGenerationResponse, WorkspaceMeetingResponse,
)
from app.services.ai import AIUnavailableError, answer_question, generate_summary
from app.services.transcripts import TranscriptParseError, parse_transcript
from app.services.workspace import (
    _commit, create_action, create_meeting, create_note, get_workspace_meeting, search_meetings,
    transcript_context, update_action, update_meeting, update_note,
)

router = APIRouter(prefix="/api/v1", tags=["workspace"])


def _meeting(session: Session, meeting_id: int) -> Meeting:
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.get("/meetings/{meeting_id}/workspace", response_model=WorkspaceMeetingResponse)
def workspace(meeting_id: int, session: Annotated[Session, Depends(get_db)]) -> WorkspaceMeetingResponse:
    result = get_workspace_meeting(session, meeting_id)
    if not result: raise HTTPException(status_code=404, detail="Meeting not found")
    return result


@router.post("/meetings", response_model=WorkspaceMeetingResponse, status_code=status.HTTP_201_CREATED)
def create_meeting_route(payload: MeetingPayload, session: Annotated[Session, Depends(get_db)]) -> WorkspaceMeetingResponse:
    try: return create_meeting(session, payload)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/meetings/{meeting_id}", response_model=WorkspaceMeetingResponse)
def edit_meeting(meeting_id: int, payload: MeetingPatch, session: Annotated[Session, Depends(get_db)]) -> WorkspaceMeetingResponse:
    try: return update_meeting(session, _meeting(session, meeting_id), payload)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/meetings/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(meeting_id: int, session: Annotated[Session, Depends(get_db)]) -> Response:
    session.delete(_meeting(session, meeting_id)); session.commit(); return Response(status_code=204)


@router.get("/meetings/{meeting_id}/transcript", response_model=list[TranscriptSegmentResponse])
def transcript(meeting_id: int, session: Annotated[Session, Depends(get_db)]) -> list[TranscriptSegment]:
    _meeting(session, meeting_id)
    return session.scalars(select(TranscriptSegment).where(TranscriptSegment.meeting_id == meeting_id).order_by(TranscriptSegment.sequence_number)).all()


@router.post("/meetings/{meeting_id}/recording", response_model=WorkspaceMeetingResponse)
async def upload_recording(meeting_id: int, session: Annotated[Session, Depends(get_db)], file: UploadFile = File(...)) -> WorkspaceMeetingResponse:
    allowed = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4", "audio/ogg", "audio/webm"}
    extension = Path(file.filename or "").suffix.lower()
    if extension not in {".mp3", ".wav", ".m4a", ".ogg", ".webm"} or (file.content_type and file.content_type not in allowed):
        raise HTTPException(status_code=415, detail="Supported audio files are MP3, WAV, M4A, OGG, and WebM")
    content = await file.read(50 * 1024 * 1024 + 1)
    if not content or len(content) > 50 * 1024 * 1024: raise HTTPException(status_code=413, detail="Audio files must be between 1 byte and 50 MB")
    destination = Path(settings.upload_dir) / "recordings"; destination.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"; (destination / filename).write_bytes(content)
    meeting = _meeting(session, meeting_id); meeting.recording_url = f"/media/recordings/{filename}"; meeting.recording_type = file.content_type or "audio/mpeg"; _commit(session)
    return get_workspace_meeting(session, meeting_id)  # type: ignore[return-value]


@router.post("/transcripts/upload", response_model=WorkspaceMeetingResponse, status_code=status.HTTP_201_CREATED)
async def upload_transcript(
    session: Annotated[Session, Depends(get_db)], file: UploadFile = File(...), title: str = Form(...),
    meeting_date: str = Form(...), description: str = Form(default=""),
) -> WorkspaceMeetingResponse:
    try:
        parsed = parse_transcript(file.filename or "", await file.read())
        date_value = datetime.fromisoformat(meeting_date.replace("Z", "+00:00"))
        if date_value.tzinfo is None: raise ValueError("meeting_date must include a timezone")
    except (TranscriptParseError, ValueError) as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        meeting = Meeting(title=title.strip(), description=description, meeting_date=date_value.astimezone(timezone.utc), duration_seconds=max(item.end_time_ms for item in parsed) // 1000, source="transcript_upload")
        session.add(meeting); session.flush(); participants: dict[str, Participant] = {}
        for item in parsed:
            participant = None
            if item.speaker:
                key = item.speaker.lower(); participant = participants.get(key) or session.scalar(select(Participant).where(Participant.name == item.speaker))
                if not participant: participant = Participant(name=item.speaker); session.add(participant); session.flush()
                participants[key] = participant
                if participant not in meeting.participants: meeting.participant_links.append(__import__("app.models", fromlist=["MeetingParticipant"]).MeetingParticipant(participant=participant))
            meeting.transcript_segments.append(TranscriptSegment(participant=participant, start_time_ms=item.start_time_ms, end_time_ms=item.end_time_ms, text=item.text, sequence_number=len(meeting.transcript_segments)))
        _commit(session)
    except Exception:
        session.rollback(); raise
    return get_workspace_meeting(session, meeting.id)  # type: ignore[return-value]


@router.get("/meetings/{meeting_id}/summary", response_model=MeetingSummaryResponse)
def get_summary(meeting_id: int, session: Annotated[Session, Depends(get_db)]) -> MeetingSummary:
    summary = session.scalar(select(MeetingSummary).where(MeetingSummary.meeting_id == meeting_id))
    if not summary: raise HTTPException(status_code=404, detail="Summary not found")
    return summary


@router.post("/meetings/{meeting_id}/summary/generate", response_model=SummaryGenerationResponse)
def regenerate_summary(meeting_id: int, session: Annotated[Session, Depends(get_db)]) -> MeetingSummary:
    meeting = get_workspace_meeting(session, meeting_id)
    if not meeting: raise HTTPException(status_code=404, detail="Meeting not found")
    try: generated = generate_summary("\n".join(item.text for item in meeting.transcript_segments))
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AIUnavailableError as exc: raise HTTPException(status_code=503, detail=str(exc)) from exc
    summary = session.scalar(select(MeetingSummary).where(MeetingSummary.meeting_id == meeting_id))
    if summary: summary.overview, summary.key_points, summary.decisions, summary.generated_by = generated.overview, generated.key_points, generated.decisions, "gemini"
    else: summary = MeetingSummary(meeting_id=meeting_id, overview=generated.overview, key_points=generated.key_points, decisions=generated.decisions, generated_by="gemini"); session.add(summary)
    _commit(session); return summary


@router.get("/meetings/{meeting_id}/action-items", response_model=list[ActionItemResponse])
def actions(meeting_id: int, session: Annotated[Session, Depends(get_db)]) -> list[ActionItem]:
    _meeting(session, meeting_id); return session.scalars(select(ActionItem).where(ActionItem.meeting_id == meeting_id).order_by(ActionItem.created_at)).all()


@router.post("/meetings/{meeting_id}/action-items", response_model=ActionItemResponse, status_code=201)
def add_action(meeting_id: int, payload: ActionItemPayload, session: Annotated[Session, Depends(get_db)]) -> ActionItem:
    try: return create_action(session, _meeting(session, meeting_id), payload)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/action-items/{action_id}", response_model=ActionItemResponse)
def edit_action(action_id: int, payload: ActionItemPatch, session: Annotated[Session, Depends(get_db)]) -> ActionItem:
    item = session.get(ActionItem, action_id)
    if not item: raise HTTPException(status_code=404, detail="Action item not found")
    try: return update_action(session, item, payload)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/action-items/{action_id}", status_code=204)
def delete_action(action_id: int, session: Annotated[Session, Depends(get_db)]) -> Response:
    item = session.get(ActionItem, action_id)
    if not item: raise HTTPException(status_code=404, detail="Action item not found")
    session.delete(item); session.commit(); return Response(status_code=204)


@router.get("/meetings/{meeting_id}/chapters", response_model=list[ChapterResponse])
def chapters(meeting_id: int, session: Annotated[Session, Depends(get_db)]):
    result = get_workspace_meeting(session, meeting_id)
    if not result: raise HTTPException(status_code=404, detail="Meeting not found")
    return result.chapters


@router.get("/meetings/{meeting_id}/notes", response_model=list[NoteResponse])
def notes(meeting_id: int, session: Annotated[Session, Depends(get_db)]) -> list[MeetingNote]:
    _meeting(session, meeting_id); return session.scalars(select(MeetingNote).where(MeetingNote.meeting_id == meeting_id).order_by(MeetingNote.created_at)).all()


@router.post("/meetings/{meeting_id}/notes", response_model=NoteResponse, status_code=201)
def add_note(meeting_id: int, payload: NoteCreate, session: Annotated[Session, Depends(get_db)]) -> MeetingNote:
    return create_note(session, _meeting(session, meeting_id), payload)


@router.patch("/notes/{note_id}", response_model=NoteResponse)
def edit_note(note_id: int, payload: NoteUpdate, session: Annotated[Session, Depends(get_db)]) -> MeetingNote:
    note = session.get(MeetingNote, note_id)
    if not note: raise HTTPException(status_code=404, detail="Note not found")
    return update_note(session, note, payload)


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, session: Annotated[Session, Depends(get_db)]) -> Response:
    note = session.get(MeetingNote, note_id)
    if not note: raise HTTPException(status_code=404, detail="Note not found")
    session.delete(note); session.commit(); return Response(status_code=204)


@router.get("/search", response_model=SearchResponse)
def search(q: str, session: Annotated[Session, Depends(get_db)]) -> SearchResponse:
    if len(q.strip()) < 2: raise HTTPException(status_code=422, detail="Search query must be at least 2 characters")
    return search_meetings(session, q)


@router.post("/meetings/{meeting_id}/ask", response_model=AskResponse)
def ask(meeting_id: int, payload: AskRequest, session: Annotated[Session, Depends(get_db)]) -> AskResponse:
    meeting = get_workspace_meeting(session, meeting_id)
    if not meeting: raise HTTPException(status_code=404, detail="Meeting not found")
    # Fetch ORM relations once to build server-side context; credentials never leave the backend.
    from app.services.workspace import get_workspace_meeting as _unused
    orm_meeting = session.scalar(select(Meeting).where(Meeting.id == meeting_id))
    if not orm_meeting: raise HTTPException(status_code=404, detail="Meeting not found")
    context = f"Summary: {meeting.summary.overview if meeting.summary else 'None'}\n" + "\n".join(segment.text for segment in meeting.transcript_segments) + "\nActions: " + ", ".join(item.title for item in meeting.action_items)
    try: return AskResponse(answer=answer_question(context, payload.question), provider="gemini")
    except AIUnavailableError as exc: raise HTTPException(status_code=503, detail=str(exc)) from exc


def _safe_filename(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-") or "meeting"


@router.get("/meetings/{meeting_id}/export/transcript")
def export_transcript(meeting_id: int, format: Literal["txt", "markdown"] = "txt", session: Annotated[Session, Depends(get_db)] = None) -> Response:
    meeting = get_workspace_meeting(session, meeting_id)
    if not meeting: raise HTTPException(status_code=404, detail="Meeting not found")
    lines = [f"# {meeting.title}", ""] if format == "markdown" else []
    lines += [f"[{segment.start_time_ms // 1000}s] {segment.participant.name if segment.participant else 'Unidentified'}: {segment.text}" for segment in meeting.transcript_segments]
    suffix, media = ("md", "text/markdown") if format == "markdown" else ("txt", "text/plain")
    return Response("\n".join(lines), media_type=media, headers={"Content-Disposition": f'attachment; filename="{_safe_filename(meeting.title)}-transcript.{suffix}"'})


@router.get("/meetings/{meeting_id}/export/summary")
def export_summary(meeting_id: int, format: Literal["markdown", "pdf"] = "markdown", session: Annotated[Session, Depends(get_db)] = None) -> Response:
    meeting = get_workspace_meeting(session, meeting_id)
    if not meeting or not meeting.summary: raise HTTPException(status_code=404, detail="Summary not found")
    text = f"# {meeting.title}\n\n{meeting.summary.overview}\n\n## Key points\n" + "\n".join(f"- {point}" for point in meeting.summary.key_points) + "\n\n## Decisions\n" + "\n".join(f"- {decision}" for decision in meeting.summary.decisions)
    if format == "markdown": return Response(text, media_type="text/markdown", headers={"Content-Disposition": f'attachment; filename="{_safe_filename(meeting.title)}-summary.md"'})
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError as exc: raise HTTPException(status_code=503, detail="PDF export dependency is not installed") from exc
    buffer = io.BytesIO(); pdf = canvas.Canvas(buffer, pagesize=letter); cursor = 760
    for line in text.splitlines():
        for part in [line[i:i + 92] for i in range(0, max(len(line), 1), 92)]:
            if cursor < 50: pdf.showPage(); cursor = 760
            pdf.drawString(48, cursor, part); cursor -= 16
    pdf.save(); return Response(buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{_safe_filename(meeting.title)}-summary.pdf"'})
