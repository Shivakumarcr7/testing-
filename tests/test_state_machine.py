"""Tests for the appointment booking state machine (services/orchestrator/
state_machine.py), now backed by an in-memory dict instead of Redis.

The Sarvam-backed helpers (entity extraction, LLM reply generation) are
monkeypatched so this suite runs without a real SARVAM_API_KEY or network
access.
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.orchestrator import state_machine


def _fake_extracted(**overrides):
    base = {
        "wants_to_book": False,
        "doctor_name": None,
        "appointment_date": None,
        "appointment_time": None,
        "confirms_booking": None,
    }
    base.update(overrides)
    return base


def test_no_redis_import():
    """The whole point of this change: no redis dependency at all."""
    import services.orchestrator.state_machine as sm

    assert "redis" not in sys.modules or not hasattr(sm, "redis_client")
    assert not hasattr(sm, "redis_client")


def test_normal_question_routes_to_llm(monkeypatch):
    """A message with no booking intent and no active booking should go
    straight to the general LLM reply, not the state machine."""

    monkeypatch.setattr(
        state_machine, "extract_booking_fields", lambda text: _fake_extracted()
    )
    monkeypatch.setattr(
        state_machine, "generate_reply", lambda text, lang: "General hospital reply"
    )

    session_id = str(uuid.uuid4())
    reply = state_machine.handle_turn(session_id, "en", "What are your visiting hours?")

    assert reply == "General hospital reply"


def test_full_booking_flow_persists_in_memory_only(monkeypatch):
    """Drive doctor -> date -> time -> confirm through three turns and check
    the appointment lands in the (mocked) demo conversation client."""

    session_id = str(uuid.uuid4())

    turns = iter(
        [
            _fake_extracted(
                wants_to_book=True,
                doctor_name="Cardiology",
                appointment_date="2026-09-20",
            ),
            _fake_extracted(appointment_time="15:00"),
            _fake_extracted(confirms_booking=True),
        ]
    )
    monkeypatch.setattr(
        state_machine, "extract_booking_fields", lambda text: next(turns)
    )

    created_appointments = []

    def fake_create_appointment(**kwargs):
        created_appointments.append(kwargs)
        return {"appointment_id": "fake-id", **kwargs}

    monkeypatch.setattr(state_machine, "create_appointment", fake_create_appointment)

    reply1 = state_machine.handle_turn(session_id, "en", "Book me with cardiology on 2026-09-20")
    assert "time" in reply1.lower()

    reply2 = state_machine.handle_turn(session_id, "en", "3 PM")
    assert "confirm" in reply2.lower()

    reply3 = state_machine.handle_turn(session_id, "en", "yes")
    assert "confirmed" in reply3.lower()

    assert len(created_appointments) == 1
    assert created_appointments[0]["doctor_name"] == "Cardiology"
    assert created_appointments[0]["appointment_datetime"] == "2026-09-20T15:00:00+05:30"

    # Booking state is cleared after completion -- a fresh turn with no
    # booking intent should fall through to the general LLM again.
    monkeypatch.setattr(
        state_machine, "extract_booking_fields", lambda text: _fake_extracted()
    )
    monkeypatch.setattr(
        state_machine, "generate_reply", lambda text, lang: "General hospital reply"
    )
    reply4 = state_machine.handle_turn(session_id, "en", "Thanks!")
    assert reply4 == "General hospital reply"


def test_cancelling_a_booking_clears_state(monkeypatch):
    session_id = str(uuid.uuid4())

    turns = iter(
        [
            _fake_extracted(
                wants_to_book=True,
                doctor_name="Dermatology",
                appointment_date="2026-09-21",
                appointment_time="10:00",
            ),
            _fake_extracted(confirms_booking=False),
        ]
    )
    monkeypatch.setattr(
        state_machine, "extract_booking_fields", lambda text: next(turns)
    )

    reply1 = state_machine.handle_turn(session_id, "en", "Book dermatology tomorrow 10am")
    assert "confirm" in reply1.lower()

    reply2 = state_machine.handle_turn(session_id, "en", "no, cancel it")
    assert "cancel" in reply2.lower()

    # State should be gone now.
    assert state_machine._get_session_state(session_id) is None
