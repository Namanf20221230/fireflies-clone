from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy

from app.models.base import Base
from app.models.types import UTCDateTime, utc_now


class Meeting(Base):
    __tablename__ = "meetings"
    __table_args__ = (UniqueConstraint("title", "meeting_date", name="uq_meetings_title_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    meeting_date: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    recording_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    recording_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[str] = mapped_column(String(100), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, onupdate=utc_now)

    participant_links: Mapped[list[MeetingParticipant]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    participants: AssociationProxy[list[Participant]] = association_proxy("participant_links", "participant")
    transcript_segments: Mapped[list[TranscriptSegment]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", order_by="TranscriptSegment.sequence_number"
    )
    summary: Mapped[MeetingSummary | None] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", uselist=False
    )
    action_items: Mapped[list[ActionItem]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    chapters: Mapped[list[Chapter]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", order_by="Chapter.sequence_number"
    )
    tag_links: Mapped[list[MeetingTag]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    tags: AssociationProxy[list[Tag]] = association_proxy("tag_links", "tag")
    notes: Mapped[list[MeetingNote]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", order_by="MeetingNote.created_at"
    )

    __mapper_args__ = {"eager_defaults": True}


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True, index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    meeting_links: Mapped[list[MeetingParticipant]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )
    transcript_segments: Mapped[list[TranscriptSegment]] = relationship(back_populates="participant")
    assigned_action_items: Mapped[list[ActionItem]] = relationship(back_populates="assignee")


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"

    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)

    meeting: Mapped[Meeting] = relationship(back_populates="participant_links")
    participant: Mapped[Participant] = relationship(back_populates="meeting_links")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    __table_args__ = (
        UniqueConstraint("meeting_id", "sequence_number", name="uq_transcript_meeting_sequence"),
        CheckConstraint("start_time_ms >= 0", name="ck_transcript_start_nonnegative"),
        CheckConstraint("end_time_ms >= start_time_ms", name="ck_transcript_end_after_start"),
        CheckConstraint("sequence_number >= 0", name="ck_transcript_sequence_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True)
    participant_id: Mapped[int | None] = mapped_column(ForeignKey("participants.id", ondelete="SET NULL"), nullable=True, index=True)
    start_time_ms: Mapped[int] = mapped_column(Integer)
    end_time_ms: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    sequence_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)

    meeting: Mapped[Meeting] = relationship(back_populates="transcript_segments")
    participant: Mapped[Participant | None] = relationship(back_populates="transcript_segments")


class MeetingSummary(Base):
    __tablename__ = "meeting_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), unique=True, index=True)
    overview: Mapped[str] = mapped_column(Text)
    key_points: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    decisions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    generated_by: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, onupdate=utc_now)

    meeting: Mapped[Meeting] = relationship(back_populates="summary")


class ActionItem(Base):
    __tablename__ = "action_items"
    __table_args__ = (
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name="ck_action_priority"),
        CheckConstraint("status IN ('open', 'in_progress', 'completed', 'cancelled')", name="ck_action_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("participants.id", ondelete="SET NULL"), nullable=True, index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", index=True)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, onupdate=utc_now)

    meeting: Mapped[Meeting] = relationship(back_populates="action_items")
    assignee: Mapped[Participant | None] = relationship(back_populates="assigned_action_items")


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (
        UniqueConstraint("meeting_id", "sequence_number", name="uq_chapter_meeting_sequence"),
        CheckConstraint("start_time_ms >= 0", name="ck_chapter_start_nonnegative"),
        CheckConstraint("end_time_ms >= start_time_ms", name="ck_chapter_end_after_start"),
        CheckConstraint("sequence_number >= 0", name="ck_chapter_sequence_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    start_time_ms: Mapped[int] = mapped_column(Integer)
    end_time_ms: Mapped[int] = mapped_column(Integer)
    sequence_number: Mapped[int] = mapped_column(Integer)

    meeting: Mapped[Meeting] = relationship(back_populates="chapters")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    color: Mapped[str] = mapped_column(String(20))

    meeting_links: Mapped[list[MeetingTag]] = relationship(back_populates="tag", cascade="all, delete-orphan")


class MeetingTag(Base):
    __tablename__ = "meeting_tags"

    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    meeting: Mapped[Meeting] = relationship(back_populates="tag_links")
    tag: Mapped[Tag] = relationship(back_populates="meeting_links")


class MeetingNote(Base):
    __tablename__ = "meeting_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, onupdate=utc_now)

    meeting: Mapped[Meeting] = relationship(back_populates="notes")
