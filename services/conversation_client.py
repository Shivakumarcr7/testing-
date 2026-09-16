"""
DEMO CONVERSATION/APPOINTMENT BACKEND -- TEMPORARY.

This client normally wraps Team C's Conversation Service (sessions, turns,
appointments) over REST, backed by Postgres/Supabase. For this standalone
deployment/testing phase we are NOT depending on Team C's database/backend,
so every function below is backed by services.demo_store instead: plain
in-memory dicts/lists, no database, no persistence across restarts.

Function signatures and return shapes are kept identical to the original
Team C-backed client, so services/gateway/main.py and
services/orchestrator/state_machine.py did not need to change. To restore
the real Team C integration later, swap these bodies back to HTTP calls
against TEAM_C_BASE_URL (see git history for the original implementation).
"""
from services.demo_store import (
    demo_create_session,
    demo_add_turn,
    demo_get_turns,
    demo_get_session,
    demo_create_appointment,
)


def create_session(user_id: str, channel: str, language: str, uhid: str | None = None) -> dict:
    """
    DEMO -- TEMPORARY. Create a new in-memory conversation session.
    channel must be 'phone', 'sms', or 'web'.
    Returns the full session dict, including the generated 'session_id'.
    """
    return demo_create_session(user_id, channel, language, uhid)


def add_turn(
    session_id: str,
    speaker: str,
    content: str,
    language: str,
    input_text: str | None = None,
    response_text: str | None = None,
) -> dict:
    """
    DEMO -- TEMPORARY. Log one conversation turn in memory against an
    existing session. speaker must be 'user', 'assistant', or 'system'.

    Convention used by the gateway: each exchange is logged as TWO
    turns -- one speaker='user' turn (content=input_text=what the
    patient said) and one speaker='assistant' turn (content=
    response_text=what the bot replied) -- rather than packing both
    directions into a single turn row.
    """
    return demo_add_turn(
        session_id,
        speaker,
        content,
        language,
        input_text=input_text,
        response_text=response_text,
    )


def get_turns(session_id: str) -> list[dict]:
    """DEMO -- TEMPORARY. Fetch all in-memory turns for a session, in order."""
    return demo_get_turns(session_id)


def get_session(session_id: str) -> dict:
    """DEMO -- TEMPORARY. Fetch an in-memory session's metadata (does not
    include turns)."""
    return demo_get_session(session_id)


def create_appointment(
    session_id: str,
    patient_uhid: str,
    doctor_name: str,
    appointment_datetime: str,
    status: str = "pending",
    booking_info: dict | None = None,
) -> dict:
    """
    DEMO -- TEMPORARY. Store an appointment in memory instead of Team C's
    ai_appointments table. appointment_datetime must be an ISO 8601 string
    (e.g. '2026-08-28T10:30:00+05:30'). patient_uhid and doctor_name are
    required.
    """
    return demo_create_appointment(
        session_id=session_id,
        patient_uhid=patient_uhid,
        doctor_name=doctor_name,
        appointment_datetime=appointment_datetime,
        status=status,
        booking_info=booking_info,
    )
