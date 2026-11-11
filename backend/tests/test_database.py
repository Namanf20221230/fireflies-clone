from datetime import date

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    ActionItem,
    Chapter,
    Meeting,
    MeetingParticipant,
    MeetingSummary,
    MeetingTag,
    Participant,
    Tag,
    TranscriptSegment,
)
from app.services.seed import seed_database, seed_stats


def test_database_initialisation_uses_migrations(session: Session) -> None:
    table_names = set(inspect(session.bind).get_table_names())
    assert {"meetings", "participants", "meeting_participants", "transcript_segments", "meeting_summaries", "action_items", "chapters", "tags", "meeting_tags"} <= table_names
    assert session.execute(text("PRAGMA foreign_keys")).scalar_one() == 1


def test_meeting_creation_and_utc_timestamp(session: Session, meeting: Meeting) -> None:
    fetched = session.get(Meeting, meeting.id)
    assert fetched is not None
    assert fetched.title == "Test Planning Meeting"
    assert fetched.meeting_date.tzinfo is not None


def test_participant_relationships(session: Session, meeting: Meeting, participant: Participant) -> None:
    session.add(MeetingParticipant(meeting=meeting, participant=participant, role="owner"))
    session.commit()

    assert meeting.participant_links[0].role == "owner"
    assert meeting.participants[0].email == "participant@example.com"


def test_transcript_segment_ordering(session: Session, meeting: Meeting, participant: Participant) -> None:
    session.add_all([
        TranscriptSegment(meeting=meeting, participant=participant, start_time_ms=1000, end_time_ms=2000, text="Second segment.", sequence_number=1),
        TranscriptSegment(meeting=meeting, participant=participant, start_time_ms=0, end_time_ms=900, text="First segment.", sequence_number=0),
    ])
    session.commit()
    session.refresh(meeting)

    assert [segment.sequence_number for segment in meeting.transcript_segments] == [0, 1]


def test_summary_relationship(session: Session, meeting: Meeting) -> None:
    summary = MeetingSummary(meeting=meeting, overview="A concise planning outcome.", key_points=[{"point": "Prioritize reliability."}], decisions=[{"decision": "Ship the fix first."}], generated_by="test")
    session.add(summary)
    session.commit()

    assert meeting.summary is not None
    assert meeting.summary.decisions[0]["decision"] == "Ship the fix first."


def test_action_item_completion_status(session: Session, meeting: Meeting, participant: Participant) -> None:
    action = ActionItem(meeting=meeting, title="Close the planning task", assignee=participant, due_date=date(2026, 7, 2), priority="high", status="open")
    session.add(action)
    session.commit()
    action.status = "completed"
    session.commit()

    assert session.get(ActionItem, action.id).status == "completed"


def test_chapter_ordering(session: Session, meeting: Meeting) -> None:
    session.add_all([
        Chapter(meeting=meeting, title="Second", description="", start_time_ms=500, end_time_ms=1000, sequence_number=1),
        Chapter(meeting=meeting, title="First", description="", start_time_ms=0, end_time_ms=499, sequence_number=0),
    ])
    session.commit()
    session.refresh(meeting)

    assert [chapter.title for chapter in meeting.chapters] == ["First", "Second"]


def test_tag_relationships(session: Session, meeting: Meeting) -> None:
    tag = Tag(name="Database", color="#2563EB")
    session.add_all([tag, MeetingTag(meeting=meeting, tag=tag)])
    session.commit()

    assert meeting.tags[0].name == "Database"


def test_meeting_cascade_deletion(session: Session, meeting: Meeting, participant: Participant) -> None:
    tag = Tag(name="Cascade", color="#000000")
    session.add_all([
        MeetingParticipant(meeting=meeting, participant=participant),
        TranscriptSegment(meeting=meeting, participant=participant, start_time_ms=0, end_time_ms=1, text="Delete with meeting.", sequence_number=0),
        MeetingSummary(meeting=meeting, overview="Delete with meeting.", key_points=[], decisions=[], generated_by="test"),
        ActionItem(meeting=meeting, title="Delete with meeting", status="open", priority="low"),
        Chapter(meeting=meeting, title="Delete with meeting", description="", start_time_ms=0, end_time_ms=1, sequence_number=0),
        tag,
        MeetingTag(meeting=meeting, tag=tag),
    ])
    session.commit()
    meeting_id = meeting.id
    session.delete(meeting)
    session.commit()

    assert session.get(Meeting, meeting_id) is None
    assert session.scalar(select(TranscriptSegment).where(TranscriptSegment.meeting_id == meeting_id)) is None
    assert session.scalar(select(ActionItem).where(ActionItem.meeting_id == meeting_id)) is None
    assert session.get(Participant, participant.id) is not None
    assert session.get(Tag, tag.id) is not None


def test_foreign_keys_are_enforced(session: Session) -> None:
    session.add(ActionItem(meeting_id=99999, title="Invalid foreign key", priority="low", status="open"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_seed_script_is_idempotent(session: Session) -> None:
    first = seed_database(session)
    second = seed_database(session)

    assert first == second
    assert first.meetings == 6
    assert first.transcript_segments == 60
    assert first.action_items == 18
    assert first.chapters == 12
    assert first.participants == 12
    assert seed_stats(session).tags == 8
