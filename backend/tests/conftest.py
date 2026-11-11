from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import create_database_engine
from app.models import Meeting, Participant


@pytest.fixture
def session(tmp_path: Path) -> Generator[Session, None, None]:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["database_url"] = database_url
    command.upgrade(config, "head")

    engine = create_database_engine(database_url)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    database_session = session_factory()
    try:
        yield database_session
    finally:
        database_session.close()
        engine.dispose()


@pytest.fixture
def meeting(session: Session) -> Meeting:
    item = Meeting(
        title="Test Planning Meeting",
        description="A meeting used for relational database tests.",
        meeting_date=datetime(2026, 7, 1, 9, tzinfo=timezone.utc),
        duration_seconds=1800,
        source="test",
    )
    session.add(item)
    session.commit()
    return item


@pytest.fixture
def participant(session: Session) -> Participant:
    item = Participant(name="Test Participant", email="participant@example.com")
    session.add(item)
    session.commit()
    return item
