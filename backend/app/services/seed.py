"""Repeatable development seed data for the Fireflies clone."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
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


PARTICIPANTS = {
    "maya@example.com": ("Maya Chen", "https://i.pravatar.cc/150?img=47"),
    "liam@example.com": ("Liam Patel", "https://i.pravatar.cc/150?img=12"),
    "sofia@example.com": ("Sofia Reyes", "https://i.pravatar.cc/150?img=32"),
    "noah@example.com": ("Noah Williams", "https://i.pravatar.cc/150?img=11"),
    "ava@example.com": ("Ava Thompson", "https://i.pravatar.cc/150?img=44"),
    "ethan@example.com": ("Ethan Brooks", "https://i.pravatar.cc/150?img=15"),
    "olivia@example.com": ("Olivia Martin", "https://i.pravatar.cc/150?img=49"),
    "daniel@example.com": ("Daniel Kim", "https://i.pravatar.cc/150?img=13"),
    "priya@example.com": ("Priya Nair", "https://i.pravatar.cc/150?img=45"),
    "marcus@example.com": ("Marcus Johnson", "https://i.pravatar.cc/150?img=14"),
    "helen@example.com": ("Helen Carter", "https://i.pravatar.cc/150?img=48"),
    "sam@example.com": ("Sam Rivera", "https://i.pravatar.cc/150?img=18"),
}

TAGS = {
    "Product": "#2563EB", "Engineering": "#7C3AED", "Marketing": "#DB2777",
    "Strategy": "#D97706", "Customer": "#059669", "Finance": "#0891B2",
    "Retrospective": "#4F46E5", "Planning": "#65A30D",
}

SEED_MEETINGS = [
    {
        "title": "Q3 Product Planning Workshop", "date": "2026-07-07T14:00:00+00:00", "duration": 3600,
        "description": "Prioritisation workshop for the Q3 collaboration roadmap.", "source": "zoom",
        "people": [("maya@example.com", "facilitator"), ("liam@example.com", "product manager"), ("sofia@example.com", "engineering lead")],
        "tags": ["Product", "Planning", "Strategy"],
        "overview": "The team selected shared action-item ownership and a searchable meeting library as Q3 priorities.",
        "points": ["Customer interviews consistently requested clearer ownership.", "The meeting library can reuse the current search infrastructure."],
        "decisions": ["Ship shared ownership before the meeting library.", "Run a five-customer usability study before design lock."],
        "chapters": [("Customer evidence", "Reviewed interview themes and opportunity sizing.", 0, 900000), ("Roadmap choices", "Sequenced Q3 initiatives and success measures.", 900000, 3600000)],
        "actions": [("Draft shared ownership specification", "Define roles, notifications, and permission boundaries.", "liam@example.com", "2026-07-10", "high", "in_progress"), ("Estimate meeting library search work", "Break down indexing and filters with the platform team.", "sofia@example.com", "2026-07-11", "high", "open"), ("Recruit usability-study customers", "Confirm five existing customers for prototype sessions.", "maya@example.com", "2026-07-14", "medium", "open")],
        "dialogue": [("maya@example.com", "The customer interviews point to one repeated issue: action items lose an owner once the meeting ends."), ("liam@example.com", "That is why shared ownership should lead the quarter; it solves a visible workflow gap without a platform rewrite."), ("sofia@example.com", "Engineering can support it if roles stay simple: one primary owner and optional collaborators."), ("maya@example.com", "The second strongest request was a place to find past decisions without opening every recording."), ("liam@example.com", "A searchable meeting library fits that need and can build on the indexing work already planned."), ("sofia@example.com", "We should stage the library after ownership because search filters need careful performance testing."), ("maya@example.com", "What success measure would make the ownership launch credible?"), ("liam@example.com", "I propose sixty percent of action items assigned within twenty-four hours for pilot teams."), ("sofia@example.com", "I will estimate the search work and flag any dependency on the transcript pipeline."), ("maya@example.com", "Great, Liam will draft the specification and I will recruit customers for prototype feedback.")],
    },
    {
        "title": "Engineering Standup: Transcript Pipeline", "date": "2026-07-08T09:30:00+00:00", "duration": 1500,
        "description": "Daily coordination for transcript ingestion reliability.", "source": "google_meet",
        "people": [("sofia@example.com", "engineering manager"), ("noah@example.com", "backend engineer"), ("ava@example.com", "platform engineer")],
        "tags": ["Engineering", "Planning"],
        "overview": "The team isolated a retry queue backlog and agreed on observability, a backfill, and a load test.",
        "points": ["Retries spike when vendor webhooks arrive out of order.", "The queue has sufficient capacity once duplicate events are discarded."],
        "decisions": ["Add idempotency keys before increasing worker count.", "Backfill the affected recordings after the deployment."],
        "chapters": [("Pipeline health", "Reviewed backlog, failures, and latency.", 0, 600000), ("Recovery plan", "Assigned instrumentation, backfill, and load-test work.", 600000, 1500000)],
        "actions": [("Add webhook idempotency keys", "Persist vendor event identifiers before queueing work.", "noah@example.com", "2026-07-08", "urgent", "in_progress"), ("Create backlog dashboard", "Expose retry age, duplicate rate, and processing latency.", "ava@example.com", "2026-07-09", "high", "open"), ("Plan recording backfill", "Prepare a bounded job for recordings delayed yesterday.", "sofia@example.com", "2026-07-09", "medium", "open")],
        "dialogue": [("sofia@example.com", "The retry queue is fifteen minutes behind, but the primary workers remain healthy."), ("noah@example.com", "I traced most retries to duplicate webhooks arriving after a successful transcription request."), ("ava@example.com", "The queue accepts both events because we do not persist the vendor event identifier."), ("sofia@example.com", "Can we make that check before scaling worker capacity?"), ("noah@example.com", "Yes, I can add an idempotency key and leave the existing retry policy unchanged."), ("ava@example.com", "I will add a dashboard for duplicate rate, oldest retry, and end-to-end latency."), ("sofia@example.com", "Do we know whether any customers lost recordings?"), ("noah@example.com", "No recordings were lost; forty-two are delayed and can be backfilled after deployment."), ("ava@example.com", "I will run a load test with reordered webhooks once Noah's change is in staging."), ("sofia@example.com", "Good, we will backfill only after the dashboard shows the queue draining normally.")],
    },
    {
        "title": "Fall Campaign Strategy Review", "date": "2026-07-09T16:00:00+00:00", "duration": 2700,
        "description": "Campaign narrative, channel mix, and measurement review.", "source": "zoom",
        "people": [("olivia@example.com", "marketing director"), ("liam@example.com", "product manager"), ("ethan@example.com", "growth analyst")],
        "tags": ["Marketing", "Strategy", "Product"],
        "overview": "Marketing chose a customer-proof campaign focused on faster follow-through after meetings.",
        "points": ["Case-study language outperformed feature-led headlines in prior campaigns.", "Paid search should target evaluation terms while webinars create demand."],
        "decisions": ["Use customer proof as the campaign anchor.", "Measure qualified pipeline rather than raw registrations."],
        "chapters": [("Message testing", "Compared positioning concepts and proof points.", 0, 1200000), ("Channel plan", "Allocated spend and defined success metrics.", 1200000, 2700000)],
        "actions": [("Interview Atlas customer", "Capture the before-and-after workflow for the campaign case study.", "olivia@example.com", "2026-07-15", "high", "open"), ("Build evaluation-keyword list", "Separate high-intent search terms from awareness terms.", "ethan@example.com", "2026-07-13", "medium", "in_progress"), ("Review product proof points", "Validate campaign claims against released capabilities.", "liam@example.com", "2026-07-12", "medium", "open")],
        "dialogue": [("olivia@example.com", "The strongest campaign concept is not transcription alone; it is getting decisions into follow-through."), ("liam@example.com", "That maps well to the shared ownership work and gives us a concrete product proof point."), ("ethan@example.com", "Our last tests showed customer stories drove more qualified visits than generic productivity headlines."), ("olivia@example.com", "Then the hero message should open with a real customer outcome, not a feature inventory."), ("liam@example.com", "I will review every proof point so we do not imply functionality that is still on the roadmap."), ("ethan@example.com", "For paid search, I recommend evaluation keywords and a separate webinar nurture path."), ("olivia@example.com", "What metric should decide whether the campaign is working?"), ("ethan@example.com", "Qualified pipeline is better than registrations because it accounts for audience fit."), ("liam@example.com", "Atlas has a compelling adoption story if we can secure an interview next week."), ("olivia@example.com", "I will own that interview and bring a first narrative to the next review.")],
    },
    {
        "title": "Series A Investor Update", "date": "2026-07-10T18:00:00+00:00", "duration": 3300,
        "description": "Quarterly investor discussion on growth, retention, and capital plans.", "source": "zoom",
        "people": [("maya@example.com", "chief executive officer"), ("marcus@example.com", "chief financial officer"), ("helen@example.com", "investor")],
        "tags": ["Finance", "Strategy"],
        "overview": "Leadership presented improving retention and agreed to share a cohort analysis before discussing additional hiring.",
        "points": ["Expansion revenue rose with multi-team adoption.", "Cash runway supports the current plan through the next planning cycle."],
        "decisions": ["Keep hiring focused on reliability and enterprise onboarding.", "Send an updated cohort analysis to investors within one week."],
        "chapters": [("Business performance", "Covered revenue, retention, and customer expansion.", 0, 1650000), ("Capital plan", "Discussed runway, hiring discipline, and reporting.", 1650000, 3300000)],
        "actions": [("Prepare cohort retention analysis", "Show adoption and expansion by customer cohort.", "marcus@example.com", "2026-07-17", "high", "open"), ("Share reliability hiring plan", "Document the roles tied directly to platform resilience.", "maya@example.com", "2026-07-16", "medium", "open"), ("Update investor metric pack", "Add meeting-library adoption and enterprise onboarding metrics.", "marcus@example.com", "2026-07-15", "medium", "in_progress")],
        "dialogue": [("maya@example.com", "This quarter's expansion came mostly from customers adding a second team after their first month."), ("marcus@example.com", "Net retention improved because those teams are using action items, not just recordings."), ("helen@example.com", "Can you separate product-led expansion from the accounts receiving concierge onboarding?"), ("marcus@example.com", "Yes, the cohort view is drafted but needs another week of validation."), ("maya@example.com", "Our hiring plan stays narrow: reliability and enterprise onboarding are the two roles tied to growth."), ("helen@example.com", "That discipline is reassuring; what does runway look like under the current plan?"), ("marcus@example.com", "We have runway through the next planning cycle without assuming a new round."), ("helen@example.com", "Please include the cohort analysis in the next investor packet."), ("maya@example.com", "We will also add adoption metrics for the meeting library as it enters pilot."), ("marcus@example.com", "I will send the updated metric pack and retention analysis by next Friday.")],
    },
    {
        "title": "Sprint 24 Retrospective", "date": "2026-07-11T15:00:00+00:00", "duration": 3000,
        "description": "Retrospective on delivery flow, quality, and team agreements.", "source": "google_meet",
        "people": [("sofia@example.com", "engineering manager"), ("ava@example.com", "platform engineer"), ("daniel@example.com", "quality engineer"), ("priya@example.com", "product designer")],
        "tags": ["Engineering", "Retrospective", "Planning"],
        "overview": "The team identified late scope changes and incomplete acceptance criteria as the main causes of spillover.",
        "points": ["Early QA pairing caught defects before implementation was complete.", "Scope changes lacked a shared decision record."],
        "decisions": ["Require acceptance criteria before sprint commitment.", "Log scope changes in the planning document with an owner."],
        "chapters": [("What helped", "Discussed successful QA pairing and smaller pull requests.", 0, 1500000), ("What to improve", "Set agreements for scope changes and ready work.", 1500000, 3000000)],
        "actions": [("Add acceptance-criteria checklist", "Add the checklist to sprint planning tickets.", "priya@example.com", "2026-07-14", "high", "open"), ("Create scope-change log", "Add a lightweight decision section to the planning document.", "sofia@example.com", "2026-07-14", "medium", "open"), ("Schedule QA pairing block", "Reserve a recurring early-sprint testing session.", "daniel@example.com", "2026-07-15", "medium", "completed")],
        "dialogue": [("sofia@example.com", "We completed most committed work, but two stories rolled because acceptance criteria changed mid-sprint."), ("priya@example.com", "The design details were available, yet the edge cases were not written into the ticket."), ("daniel@example.com", "Pairing with engineers on day two caught three issues before they became late test failures."), ("ava@example.com", "Smaller pull requests also made those conversations much easier to resolve quickly."), ("sofia@example.com", "Where did the scope changes originate?"), ("priya@example.com", "They were reasonable customer requests, but we did not record who approved the tradeoff."), ("daniel@example.com", "A checklist before commitment would give QA a clear readiness signal."), ("ava@example.com", "And a scope-change log would stop us from rediscovering the same decision in standup."), ("sofia@example.com", "Let's make both changes for Sprint 25 and preserve the early QA pairing block."), ("priya@example.com", "I will add the checklist while Daniel documents the pairing cadence.")],
    },
    {
        "title": "Northstar Customer Feedback Session", "date": "2026-07-12T17:30:00+00:00", "duration": 2400,
        "description": "Structured feedback interview with Northstar's operations team.", "source": "zoom",
        "people": [("liam@example.com", "product manager"), ("sam@example.com", "customer success manager"), ("helen@example.com", "customer operations lead")],
        "tags": ["Customer", "Product", "Strategy"],
        "overview": "Northstar values searchable decisions but needs simpler sharing controls and clearer follow-up ownership.",
        "points": ["Operations managers search decisions after weekly cross-functional meetings.", "External sharing requires confidence that sensitive sections can be excluded."],
        "decisions": ["Prototype section-level sharing controls.", "Invite Northstar to validate ownership reminders in the pilot."],
        "chapters": [("Current workflow", "Mapped how Northstar captures and retrieves decisions.", 0, 1000000), ("Prototype feedback", "Discussed sharing controls and ownership reminders.", 1000000, 2400000)],
        "actions": [("Design section-level sharing prototype", "Explore excluding sensitive transcript sections from shared views.", "liam@example.com", "2026-07-18", "high", "open"), ("Invite Northstar to ownership pilot", "Confirm two operations managers for the pilot group.", "sam@example.com", "2026-07-16", "medium", "in_progress"), ("Document decision-search workflow", "Capture exact queries and filters used after weekly meetings.", "helen@example.com", "2026-07-15", "medium", "open")],
        "dialogue": [("sam@example.com", "Northstar uses meeting notes most heavily after cross-functional planning sessions."), ("helen@example.com", "We search for decisions when a team asks why a priority changed two weeks later."), ("liam@example.com", "Does the current transcript search get you to that answer quickly enough?"), ("helen@example.com", "Usually, but sharing a full recording externally is too broad when one section is sensitive."), ("sam@example.com", "They need confidence that an operations summary can be shared without exposing personnel discussions."), ("liam@example.com", "We are considering section-level sharing; would that match your workflow?"), ("helen@example.com", "Yes, especially if the shared view keeps the decision and its owner together."), ("sam@example.com", "The ownership pilot could also test reminders for tasks that remain unassigned."), ("liam@example.com", "I will prototype the sharing controls and use your exact search queries in usability tests."), ("helen@example.com", "We can nominate two managers to try the pilot next week.")],
    },
]


@dataclass(frozen=True)
class SeedStats:
    meetings: int
    participants: int
    transcript_segments: int
    action_items: int
    chapters: int
    tags: int


def seed_database(session: Session) -> SeedStats:
    """Insert the fixture set once; existing meetings are left untouched."""
    try:
        people = _ensure_participants(session)
        tags = _ensure_tags(session)
        for payload in SEED_MEETINGS:
            meeting_date = datetime.fromisoformat(payload["date"])
            existing = session.scalar(select(Meeting).where(Meeting.title == payload["title"], Meeting.meeting_date == meeting_date))
            if existing is not None:
                continue
            meeting = Meeting(title=payload["title"], description=payload["description"], meeting_date=meeting_date, duration_seconds=payload["duration"], source=payload["source"])
            session.add(meeting)
            session.flush()
            for email, role in payload["people"]:
                session.add(MeetingParticipant(meeting=meeting, participant=people[email], role=role))
            for sequence, (email, text) in enumerate(payload["dialogue"]):
                session.add(TranscriptSegment(meeting=meeting, participant=people[email], start_time_ms=sequence * 120000, end_time_ms=(sequence + 1) * 120000 - 1000, text=text, sequence_number=sequence))
            session.add(MeetingSummary(meeting=meeting, overview=payload["overview"], key_points=[{"point": point} for point in payload["points"]], decisions=[{"decision": decision} for decision in payload["decisions"]], generated_by="seed-data"))
            for title, description, email, due_date, priority, status in payload["actions"]:
                session.add(ActionItem(meeting=meeting, title=title, description=description, assignee=people[email], due_date=date.fromisoformat(due_date), priority=priority, status=status))
            for sequence, (title, description, start_ms, end_ms) in enumerate(payload["chapters"]):
                session.add(Chapter(meeting=meeting, title=title, description=description, start_time_ms=start_ms, end_time_ms=end_ms, sequence_number=sequence))
            for tag_name in payload["tags"]:
                session.add(MeetingTag(meeting=meeting, tag=tags[tag_name]))
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    return seed_stats(session)


def seed_stats(session: Session) -> SeedStats:
    return SeedStats(
        meetings=session.scalar(select(func.count()).select_from(Meeting)) or 0,
        participants=session.scalar(select(func.count()).select_from(Participant)) or 0,
        transcript_segments=session.scalar(select(func.count()).select_from(TranscriptSegment)) or 0,
        action_items=session.scalar(select(func.count()).select_from(ActionItem)) or 0,
        chapters=session.scalar(select(func.count()).select_from(Chapter)) or 0,
        tags=session.scalar(select(func.count()).select_from(Tag)) or 0,
    )


def _ensure_participants(session: Session) -> dict[str, Participant]:
    result: dict[str, Participant] = {}
    for email, (name, avatar_url) in PARTICIPANTS.items():
        participant = session.scalar(select(Participant).where(Participant.email == email))
        if participant is None:
            participant = Participant(name=name, email=email, avatar_url=avatar_url)
            session.add(participant)
            session.flush()
        result[email] = participant
    return result


def _ensure_tags(session: Session) -> dict[str, Tag]:
    result: dict[str, Tag] = {}
    for name, color in TAGS.items():
        tag = session.scalar(select(Tag).where(Tag.name == name))
        if tag is None:
            tag = Tag(name=name, color=color)
            session.add(tag)
            session.flush()
        result[name] = tag
    return result


def main() -> None:
    with SessionLocal() as session:
        stats = seed_database(session)
    print(f"Seeded {stats.meetings} meetings, {stats.participants} participants, {stats.transcript_segments} transcript segments, {stats.action_items} action items, {stats.chapters} chapters, and {stats.tags} tags.")


if __name__ == "__main__":
    main()
