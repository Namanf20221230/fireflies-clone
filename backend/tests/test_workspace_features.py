import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Meeting, MeetingNote, Participant
from app.schemas.workspace import ActionItemPatch, ActionItemPayload, NoteCreate
from app.services.ai import AIUnavailableError, generate_summary
from app.services.transcripts import TranscriptParseError, parse_transcript
from app.services.workspace import create_action, create_note, update_action


def test_txt_vtt_and_json_transcripts_parse_in_time_order() -> None:
    txt = b"[00:00:05.000 - 00:00:07.000] Maya: Second\n[00:00:00.000 - 00:00:04.000] Liam: First"
    vtt = b"WEBVTT\n\n00:00:00.000 --> 00:00:02.000\n<v Maya>Hello\n"
    json_data = b'[{"speaker":"Maya","start_time_ms":0,"end_time_ms":1000,"text":"Hello"}]'
    assert [item.text for item in parse_transcript("a.txt", txt)] == ["First", "Second"]
    assert parse_transcript("a.vtt", vtt)[0].speaker == "Maya"
    assert parse_transcript("a.json", json_data)[0].end_time_ms == 1000


@pytest.mark.parametrize("name,data", [("bad.txt", b"not a timed line"), ("bad.vtt", b"broken"), ("bad.json", b"{}")])
def test_invalid_transcripts_are_rejected(name: str, data: bytes) -> None:
    with pytest.raises(TranscriptParseError):
        parse_transcript(name, data)


def test_notes_actions_and_cascade_are_persistent(session: Session, meeting: Meeting, participant: Participant) -> None:
    note = create_note(session, meeting, NoteCreate(content="Follow up with legal."))
    action = create_action(session, meeting, ActionItemPayload(title="Send update", assignee_id=participant.id))
    update_action(session, action, ActionItemPatch(status="completed"))
    assert session.get(MeetingNote, note.id).content == "Follow up with legal."
    assert session.get(type(action), action.id).status == "completed"
    meeting_id = meeting.id; session.delete(meeting); session.commit()
    assert session.scalar(select(MeetingNote).where(MeetingNote.meeting_id == meeting_id)) is None


def test_gemini_generation_requires_configured_credentials() -> None:
    with pytest.raises(AIUnavailableError):
        generate_summary("Maya: We decided to ship on Friday.")
