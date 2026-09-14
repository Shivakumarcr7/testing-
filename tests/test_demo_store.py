"""Tests for the in-memory demo backend that replaces Team C.

No external services (Team C, Postgres, Supabase, Redis) or network access
are required -- everything here is plain Python state.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from services import demo_store


def test_demo_login_rejects_malformed_number():
    with pytest.raises(demo_store.InvalidPhoneNumber):
        demo_store.demo_login("12345")


def test_demo_login_rejects_non_indian_looking_number():
    """Must start 6-9 and be exactly 10 digits."""
    with pytest.raises(demo_store.InvalidPhoneNumber):
        demo_store.demo_login("1234567890")


def test_demo_login_registers_new_number_once():
    phone = "9876500001"

    first = demo_store.demo_login(phone)
    assert first["is_new"] is True
    assert first["phone_no"] == phone
    assert first["auth_id"]

    second = demo_store.demo_login(phone)
    assert second["is_new"] is False
    # Same account, not a new auth_id.
    assert second["auth_id"] == first["auth_id"]


def test_create_session_and_get_session_roundtrip():
    session = demo_store.demo_create_session(
        user_id="some-auth-id", channel="web", language="en"
    )
    assert session["session_id"]
    assert session["channel"] == "web"

    fetched = demo_store.demo_get_session(session["session_id"])
    assert fetched["session_id"] == session["session_id"]


def test_get_session_raises_for_unknown_id():
    with pytest.raises(KeyError):
        demo_store.demo_get_session("does-not-exist")


def test_add_turn_and_get_turns_roundtrip():
    session = demo_store.demo_create_session(
        user_id="some-auth-id", channel="web", language="en"
    )
    session_id = session["session_id"]

    demo_store.demo_add_turn(
        session_id, "user", "hello", "en", input_text="hello"
    )
    demo_store.demo_add_turn(
        session_id, "assistant", "hi there", "en", response_text="hi there"
    )

    turns = demo_store.demo_get_turns(session_id)
    assert len(turns) == 2
    assert turns[0]["speaker"] == "user"
    assert turns[1]["speaker"] == "assistant"


def test_create_appointment_stores_it_in_memory():
    appointment = demo_store.demo_create_appointment(
        session_id="some-session",
        patient_uhid="UHID-DEMO-0001",
        doctor_name="Cardiology",
        appointment_datetime="2026-09-20T15:00:00+05:30",
        status="confirmed",
    )
    assert appointment["appointment_id"]
    assert appointment["doctor_name"] == "Cardiology"
    assert appointment["status"] == "confirmed"
