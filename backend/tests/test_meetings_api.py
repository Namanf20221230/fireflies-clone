import asyncio
from collections.abc import Generator
from datetime import datetime, timezone

import httpx
import pytest
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.models import Meeting
from app.services.seed import seed_database


@pytest.fixture
def seeded_api(session: Session) -> Generator[None, None, None]:
    seed_database(session)

    def override_get_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield
    finally:
        app.dependency_overrides.clear()


async def request(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path)


def test_meetings_list_returns_seeded_records(seeded_api: None) -> None:
    response = asyncio.run(request("/api/v1/meetings"))

    assert response.status_code == 200
    payload = response.json()
    assert {key: payload[key] for key in ("total", "page", "page_size", "total_pages")} == {"total": 6, "page": 1, "page_size": 10, "total_pages": 1}
    assert payload["items"][0]["title"] == "Northstar Customer Feedback Session"
    assert payload["items"][0]["participant_count"] >= 2
    assert payload["items"][0]["summary_preview"]
    assert {"id", "title", "description", "meeting_date", "duration_seconds", "participants", "participant_count", "tags", "summary_preview"} <= payload["items"][0].keys()
    assert payload["items"][0]["participants"][0]["name"]
    assert payload["items"][0]["tags"][0]["color"].startswith("#")


def test_meetings_searches_title_and_participant(seeded_api: None) -> None:
    title_response = asyncio.run(request("/api/v1/meetings?search=standup"))
    participant_response = asyncio.run(request("/api/v1/meetings?search=Maya%20Chen"))

    assert [item["title"] for item in title_response.json()["items"]] == ["Engineering Standup: Transcript Pipeline"]
    assert participant_response.json()["total"] == 2
    assert {item["title"] for item in participant_response.json()["items"]} == {"Q3 Product Planning Workshop", "Series A Investor Update"}
    case_insensitive_response = asyncio.run(request("/api/v1/meetings?search=StAnDuP"))
    assert case_insensitive_response.json()["total"] == 1


def test_meetings_filters_dates_and_sorts(seeded_api: None) -> None:
    filtered = asyncio.run(request("/api/v1/meetings?start_date=2026-07-09&end_date=2026-07-10&sort=oldest"))
    oldest = asyncio.run(request("/api/v1/meetings?sort=oldest"))

    assert [item["title"] for item in filtered.json()["items"]] == ["Fall Campaign Strategy Review", "Series A Investor Update"]
    assert oldest.json()["items"][0]["title"] == "Q3 Product Planning Workshop"


def test_meetings_support_individual_inclusive_date_filters(seeded_api: None) -> None:
    start_only = asyncio.run(request("/api/v1/meetings?start_date=2026-07-11"))
    end_only = asyncio.run(request("/api/v1/meetings?end_date=2026-07-08"))

    assert start_only.json()["total"] == 2
    assert end_only.json()["total"] == 2


def test_meetings_pagination(seeded_api: None) -> None:
    first_page = asyncio.run(request("/api/v1/meetings?page=1&page_size=2"))
    second_page = asyncio.run(request("/api/v1/meetings?page=2&page_size=2"))

    assert {key: first_page.json()[key] for key in ("total", "page", "page_size", "total_pages")} == {"total": 6, "page": 1, "page_size": 2, "total_pages": 3}
    first_ids = {item["id"] for item in first_page.json()["items"]}
    second_ids = {item["id"] for item in second_page.json()["items"]}
    assert len(first_ids) == len(second_ids) == 2
    assert first_ids.isdisjoint(second_ids)


def test_meetings_rejects_invalid_date_range(seeded_api: None) -> None:
    response = asyncio.run(request("/api/v1/meetings?start_date=2026-07-12&end_date=2026-07-07"))

    assert response.status_code == 422
    assert response.json()["detail"] == "start_date must be on or before end_date"


def test_meetings_rejects_invalid_pagination_and_sort(seeded_api: None) -> None:
    invalid_page = asyncio.run(request("/api/v1/meetings?page=0"))
    invalid_page_size = asyncio.run(request("/api/v1/meetings?page_size=51"))
    invalid_sort = asyncio.run(request("/api/v1/meetings?sort=alphabetical"))

    assert invalid_page.status_code == 422
    assert invalid_page_size.status_code == 422
    assert invalid_sort.status_code == 422


def test_meeting_detail_and_unknown_id(seeded_api: None) -> None:
    list_response = asyncio.run(request("/api/v1/meetings?page_size=1"))
    meeting_id = list_response.json()["items"][0]["id"]
    detail_response = asyncio.run(request(f"/api/v1/meetings/{meeting_id}"))
    missing_response = asyncio.run(request("/api/v1/meetings/99999"))

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == meeting_id
    assert detail_response.json()["source"] == "zoom"
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Meeting not found"


def test_missing_summary_returns_null_preview(seeded_api: None, session: Session) -> None:
    meeting = Meeting(
        title="Meeting Without Summary",
        description="This record intentionally has no summary.",
        meeting_date=datetime(2026, 7, 13, tzinfo=timezone.utc),
        duration_seconds=300,
        source="test",
    )
    session.add(meeting)
    session.commit()

    response = asyncio.run(request(f"/api/v1/meetings/{meeting.id}"))

    assert response.status_code == 200
    assert response.json()["summary_preview"] is None
