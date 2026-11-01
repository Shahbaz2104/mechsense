"""Test fixtures: isolated test database per test, HTTP client, factories.

Every test gets a freshly created schema (drop/create) so tests are
independently runnable and order-independent. The suite runs against
`TEST_DATABASE_URL` (never the development database).
"""

from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

settings = get_settings()


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        settings.test_database_url,
        pool_pre_ping=True,
        future=True,
        connect_args={"options": "-c TimeZone=UTC"},
    )
    yield engine
    engine.dispose()


@pytest.fixture()
def db(engine) -> Session:
    """Clean database session for one test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True
    )
    session = TestingSession()
    yield session
    session.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """HTTP client wired to the test database session."""

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def machine_payload() -> dict:
    def _make(identifier: str = "X-TEST1", **overrides) -> dict:
        payload = {
            "identifier": identifier,
            "name": f"Machine {identifier}",
            "equipment_type": "pump",
            "location": "Test Hall",
            "manufacturer": "Acme",
            "model": "T-1",
            "installation_date": "2024-01-15",
            "thresholds": {"vibration_rms": {"warning": 4.5, "critical": 7.1}},
        }
        payload.update(overrides)
        return payload

    return _make


@pytest.fixture()
def create_machine(client: TestClient, machine_payload) -> Callable[..., dict]:
    def _create(identifier: str = "X-TEST1", **overrides) -> dict:
        response = client.post("/api/v1/machines", json=machine_payload(identifier, **overrides))
        assert response.status_code == 201, response.text
        return response.json()

    return _create


@pytest.fixture()
def ingest(client: TestClient) -> Callable[..., dict]:
    """POST a reading; defaults to a quiet, under-threshold measurement."""

    def _ingest(machine_id: int, timestamp: str | None = None, **values) -> dict:
        payload = {
            "machine_id": machine_id,
            "timestamp": timestamp or "2026-01-15T10:00:00Z",
            "vibration_rms": 2.0,
            "temperature": 50.0,
            "rpm": 1480.0,
            "load_pct": 55.0,
            "pressure": None,
        }
        payload.update(values)
        response = client.post("/api/v1/readings", json=payload)
        return {"status": response.status_code, "body": response.json()}

    return _ingest


@pytest.fixture()
def add_reading(db: Session):
    """Unit-level reading factory (no HTTP): flushes and returns the row."""

    from decimal import Decimal

    from app.models import ReadingSource, SensorReading

    def _add(
        machine,
        timestamp: datetime,
        vibration: float = 2.0,
        temperature: float = 50.0,
        rpm: float = 1480.0,
        load: float = 55.0,
        pressure: float | None = None,
    ) -> SensorReading:
        reading = SensorReading(
            machine_id=machine.id,
            timestamp=timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp,
            vibration_rms=Decimal(str(vibration)),
            temperature=Decimal(str(temperature)),
            rpm=Decimal(str(rpm)),
            load_pct=Decimal(str(load)),
            pressure=Decimal(str(pressure)) if pressure is not None else None,
            source=ReadingSource.simulated,
        )
        db.add(reading)
        db.flush()
        return reading

    return _add


def error_body(response: dict) -> dict:
    """Assert-shaped access to the standard error envelope."""
    assert "error" in response, f"expected error envelope, got: {response}"
    return response["error"]
