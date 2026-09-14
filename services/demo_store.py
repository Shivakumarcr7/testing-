"""
DEMO BACKEND -- TEMPORARY.

This module stands in for Team C's Conversation/Auth Service (Postgres via
Supabase) so the voice assistant can run standalone, without Team C's
database, for deployment/testing purposes.

Everything here is kept in plain Python dicts/lists in process memory:

    - No database.
    - No persistence across restarts.
    - Not shared across multiple gateway workers/processes.
    - Not safe for concurrent production traffic.

This is intentional. The only goal is to let the full voice pipeline
(browser -> gateway -> STT -> orchestrator/LLM -> TTS -> browser) be
exercised end-to-end without depending on Team C's real database/backend.

When Team C's service is ready to be wired back in, restore the HTTP calls
in services/auth_client.py and services/conversation_client.py (git history
has the original versions) -- the function signatures and return shapes in
this module were kept identical to Team C's API on purpose, so the rest of
the codebase (gateway, orchestrator) does not need to change either way.
"""
import re
import uuid
from datetime import datetime, timezone

# =========================================================
# IN-MEMORY "TABLES"
# =========================================================

# phone_no (str) -> account dict {"auth_id", "phone_no"}
_accounts: dict[str, dict] = {}

# session_id (str) -> session dict
_sessions: dict[str, dict] = {}

# session_id (str) -> list of turn dicts
_turns: dict[str, list[dict]] = {}

# list of appointment dicts
_appointments: list[dict] = []


# A "valid-looking" 10-digit Indian mobile number: starts 6-9, 10 digits
# total. This is a shape check only -- there is no OTP/SMS verification in
# this demo flow.
_PHONE_RE = re.compile(r"^[6-9]\d{9}$")


class PhoneNotRegistered(Exception):
    """Kept for interface parity with the original Team C client; the demo
    flow self-registers instead of rejecting, so this should not fire."""


class InvalidPhoneNumber(Exception):
    """The number is not a valid-looking 10-digit Indian mobile number."""


# =========================================================
# DEMO AUTH -- TEMPORARY
# =========================================================

def demo_login(phone_no: str) -> dict:
    """
    DEMO AUTH -- TEMPORARY.

    Accepts a valid-looking 10-digit Indian phone number, creates a
    temporary in-memory account the first time it's seen, and returns it.
    There is no password, no OTP, and no real database -- this exists only
    to let the demo move past a login screen and into the voice assistant.
    """
    phone_no = (phone_no or "").strip()

    if not _PHONE_RE.match(phone_no):
        raise InvalidPhoneNumber("Please enter a valid 10-digit phone number.")

    is_new = phone_no not in _accounts

    if is_new:
        _accounts[phone_no] = {
            "auth_id": str(uuid.uuid4()),
            "phone_no": phone_no,
        }

    account = dict(_accounts[phone_no])
    account["is_new"] = is_new
    return account


# =========================================================
# DEMO SESSIONS -- TEMPORARY
# =========================================================

def demo_create_session(
    user_id: str,
    channel: str,
    language: str,
    uhid: str | None = None,
) -> dict:
    """Create an in-memory conversation session. Mirrors the shape Team C's
    POST /api/v1/sessions returned."""
    session_id = str(uuid.uuid4())

    session = {
        "session_id": session_id,
        "user_id": user_id,
        "channel": channel,
        "language": language,
        "uhid": uhid,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    _sessions[session_id] = session
    _turns[session_id] = []

    return dict(session)


def demo_get_session(session_id: str) -> dict:
    session = _sessions.get(session_id)

    if session is None:
        raise KeyError(f"No such demo session: {session_id}")

    return dict(session)


def demo_add_turn(
    session_id: str,
    speaker: str,
    content: str,
    language: str,
    input_text: str | None = None,
    response_text: str | None = None,
) -> dict:
    """Log one conversation turn in memory. Mirrors the shape Team C's
    POST /api/v1/sessions/{id}/turns returned."""
    turn = {
        "turn_id": str(uuid.uuid4()),
        "session_id": session_id,
        "speaker": speaker,
        "content": content,
        "language": language,
        "input_text": input_text,
        "response_text": response_text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    _turns.setdefault(session_id, []).append(turn)

    return dict(turn)


def demo_get_turns(session_id: str) -> list[dict]:
    return [dict(t) for t in _turns.get(session_id, [])]


# =========================================================
# DEMO APPOINTMENTS -- TEMPORARY
# =========================================================

def demo_create_appointment(
    session_id: str,
    patient_uhid: str,
    doctor_name: str,
    appointment_datetime: str,
    status: str = "pending",
    booking_info: dict | None = None,
) -> dict:
    """Store an appointment in memory instead of Team C's ai_appointments
    table. Mirrors the shape Team C's POST /api/v1/appointments returned."""
    appointment = {
        "appointment_id": str(uuid.uuid4()),
        "session_id": session_id,
        "patient_uhid": patient_uhid,
        "doctor_name": doctor_name,
        "appointment_datetime": appointment_datetime,
        "status": status,
        "booking_info": booking_info,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    _appointments.append(appointment)

    return dict(appointment)
