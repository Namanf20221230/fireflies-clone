from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.entities import MeetingDetailResponse, MeetingListResponse
from app.services.meetings import get_meeting, list_meetings


router = APIRouter(prefix="/api/v1/meetings", tags=["meetings"])


@router.get("", response_model=MeetingListResponse)
def get_meetings(
    session: Annotated[Session, Depends(get_db)],
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    start_date: date | None = None,
    end_date: date | None = None,
    sort: Literal["newest", "oldest"] = "newest",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> MeetingListResponse:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="start_date must be on or before end_date",
        )
    return list_meetings(
        session,
        search=search,
        start_date=start_date,
        end_date=end_date,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
def get_meeting_by_id(
    meeting_id: int, session: Annotated[Session, Depends(get_db)]
) -> MeetingDetailResponse:
    meeting = get_meeting(session, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting
