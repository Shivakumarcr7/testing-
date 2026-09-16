"""
Appointment booking state machine.

States:
ASK_DOCTOR -> ASK_DATE -> ASK_TIME -> CONFIRM -> COMPLETED

DEMO / TEMPORARY -- IN-MEMORY STATE:

Appointment conversation state is held in a plain Python dict in process
memory, keyed by session_id. This is intentional for the standalone demo:

    - No Redis, no external cache, no extra service to run.
    - State does NOT survive a server restart -- an in-progress booking
      conversation is lost if the process restarts.
    - State is NOT shared across multiple gateway worker processes -- run
      this service as a single worker (the Render/uvicorn default) for the
      demo, since a second worker would have its own empty dict.
    - Not safe for concurrent production traffic at scale.

An unfinished booking conversation is expired after SESSION_TTL seconds,
the same lifetime Redis's SETEX previously enforced, just checked on read
instead of relying on Redis's own expiry.

To restore Redis-backed state later (e.g. for multi-worker deployments),
reintroduce a redis.Redis.from_url(REDIS_URL) client and swap the three
helpers below back to GET/SETEX/DELETE calls (see git history).
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from services.llm.client import generate_reply
from services.conversation_client import create_appointment
from services.orchestrator.entity_extraction import extract_booking_fields
from services.orchestrator.templates import render_template


# DEMO / TEMPORARY in-memory appointment-conversation store.
# session_id -> {"state": dict, "expires_at": float (epoch seconds)}
_session_store: dict[str, dict] = {}

# Keep an unfinished appointment conversation for 1 hour.
SESSION_TTL = 3600

# The hospital runs on IST. Appointment times a patient gives are in IST, and
# must be sent with this offset attached -- see _complete_booking.
IST_UTC_OFFSET = "+05:30"


SLOT_ORDER = [
    "doctor_name",
    "appointment_date",
    "appointment_time",
]

SLOT_TO_ASK_STATE = {
    "doctor_name": "ASK_DOCTOR",
    "appointment_date": "ASK_DATE",
    "appointment_time": "ASK_TIME",
}


# Placeholder patient identifier until real patient registration/login exists.
# TODO: replace with a real UHID once auth/registration is built.
PLACEHOLDER_PATIENT_UHID = "UHID-DEMO-0001"


def _get_session_state(session_id: str) -> dict | None:
    """
    DEMO / TEMPORARY. Get appointment state from the in-memory store.

    Returns None if there is no active appointment conversation, or if the
    stored one has expired (SESSION_TTL seconds since it was last written).
    """
    entry = _session_store.get(session_id)

    if entry is None:
        return None

    if entry["expires_at"] < time.time():
        _session_store.pop(session_id, None)
        return None

    return entry["state"]


def _set_session_state(session_id: str, state: dict) -> None:
    """
    DEMO / TEMPORARY. Save appointment state to the in-memory store.

    The entry is treated as expired -- and skipped on the next read --
    after SESSION_TTL seconds. It is NOT persisted anywhere else, so a
    server restart loses all in-progress bookings.
    """
    _session_store[session_id] = {
        "state": state,
        "expires_at": time.time() + SESSION_TTL,
    }


def _delete_session_state(session_id: str) -> None:
    """
    DEMO / TEMPORARY. Delete appointment state from the in-memory store.
    """
    _session_store.pop(session_id, None)


def _first_missing_slot(slots: dict) -> str | None:
    """
    Return the first appointment field that is still missing.
    """
    for slot_name in SLOT_ORDER:
        if not slots.get(slot_name):
            return slot_name

    return None


def handle_turn(session_id: str, short_lang: str, user_text: str) -> str:
    """
    Route one conversation turn through the appointment state machine
    or normal hospital-receptionist Q&A.

    Appointment state is held in the in-memory demo store, keyed by
    session_id (see the module docstring).
    """

    # Get the current appointment state from the in-memory demo store.
    existing = _get_session_state(session_id)

    # Extract appointment information from the current message.
    extracted = extract_booking_fields(user_text)

    # Debug logging
    print(f"[Orchestrator] INPUT: {user_text}")
    print(f"[Orchestrator] EXTRACTED: {extracted}")

    # ---------------------------------------------------------
    # Normal hospital Q&A
    # ---------------------------------------------------------

    # If there is no active booking and the user isn't trying
    # to book anything, send the question to the normal LLM.
    if existing is None and not extracted["wants_to_book"]:
        print("[Orchestrator] Routing to normal LLM")
        return generate_reply(user_text, short_lang)

    # ---------------------------------------------------------
    # Start a new appointment booking
    # ---------------------------------------------------------

    if existing is None:

        slots = {
            "doctor_name": extracted["doctor_name"],
            "appointment_date": extracted["appointment_date"],
            "appointment_time": extracted["appointment_time"],
        }

        print(f"[Orchestrator] New booking slots: {slots}")

        missing = _first_missing_slot(slots)

        if missing is None:
            state = "CONFIRM"
        else:
            state = SLOT_TO_ASK_STATE[missing]

        print(f"[Orchestrator] New state: {state}")

        # Save the new booking state in the in-memory demo store.
        _set_session_state(
            session_id,
            {
                "state": state,
                "slots": slots,
            },
        )

        return _render_current_state(
            session_id,
            short_lang,
        )

    # ---------------------------------------------------------
    # Continue existing appointment booking
    # ---------------------------------------------------------

    state = existing["state"]
    slots = existing["slots"]

    print(f"[Orchestrator] Existing state: {state}")
    print(f"[Orchestrator] Existing slots: {slots}")

    # ---------------------------------------------------------
    # Confirmation state
    # ---------------------------------------------------------

    if state == "CONFIRM":

        if extracted["confirms_booking"] is True:

            print("[Orchestrator] Booking confirmed")

            return _complete_booking(
                session_id,
                short_lang,
            )

        elif extracted["confirms_booking"] is False:

            print("[Orchestrator] Booking cancelled")

            _delete_session_state(session_id)

            return render_template(
                "CANCELLED",
                short_lang,
            )

        else:

            # User's answer wasn't clearly yes/no.
            return _render_current_state(
                session_id,
                short_lang,
            )

    # ---------------------------------------------------------
    # ASK_DOCTOR / ASK_DATE / ASK_TIME
    # ---------------------------------------------------------

    # Merge newly extracted information into existing slots.
    #
    # Example:
    # User previously gave doctor name.
    # Next turn:
    # "Tomorrow at 10:30"
    #
    # The in-memory demo store keeps the doctor name and we add date/time.

    for slot_name in SLOT_ORDER:

        if extracted.get(slot_name):
            slots[slot_name] = extracted[slot_name]

    print(f"[Orchestrator] Updated slots: {slots}")

    # Determine what is still missing.
    missing = _first_missing_slot(slots)

    if missing is None:

        existing["state"] = "CONFIRM"

    else:

        existing["state"] = SLOT_TO_ASK_STATE[missing]

    print(
        f"[Orchestrator] Updated state: "
        f"{existing['state']}"
    )

    # Save updated slots/state back to the in-memory demo store.
    _set_session_state(
        session_id,
        existing,
    )

    return _render_current_state(
        session_id,
        short_lang,
    )


def _render_current_state(
    session_id: str,
    short_lang: str,
) -> str:
    """
    Read the current state from the in-memory demo store and generate the
    appropriate reply.
    """

    entry = _get_session_state(session_id)

    if entry is None:

        return render_template(
            "BOOKING_FAILED",
            short_lang,
        )

    state = entry["state"]
    slots = entry["slots"]

    print(f"[Orchestrator] Rendering state: {state}")
    print(f"[Orchestrator] Rendering slots: {slots}")

    # All appointment information has been collected.
    if state == "CONFIRM":

        return render_template(
            "CONFIRM",
            short_lang,
            doctor=slots["doctor_name"],
            date=slots["appointment_date"],
            time=slots["appointment_time"],
        )

    # Still collecting information.
    return render_template(
        state,
        short_lang,
    )


def _complete_booking(
    session_id: str,
    short_lang: str,
) -> str:
    """
    Create the appointment (in the demo in-memory store -- see
    services/conversation_client.py) and clear the temporary in-memory
    booking-conversation state.
    """

    entry = _get_session_state(session_id)

    if entry is None:

        return render_template(
            "BOOKING_FAILED",
            short_lang,
        )

    slots = entry["slots"]

    # Patients state times in IST, so stamp the offset explicitly. Sending a
    # naive timestamp let Postgres store it as UTC in the TIMESTAMPTZ column,
    # which then read back 5h30m off -- a 3:00 PM booking was saved (and
    # confirmed over WhatsApp) as 8:30 PM.
    appointment_datetime = (
        f"{slots['appointment_date']}"
        f"T{slots['appointment_time']}:00"
        f"{IST_UTC_OFFSET}"
    )

    print(
        f"[Orchestrator] Creating appointment: "
        f"{appointment_datetime}"
    )

    try:

        create_appointment(
            session_id=session_id,
            patient_uhid=PLACEHOLDER_PATIENT_UHID,
            doctor_name=slots["doctor_name"],
            appointment_datetime=appointment_datetime,
            status="confirmed",
        )

    except Exception as e:

        print(
            f"[Orchestrator] Appointment creation failed: {e}"
        )

        # Don't leave a broken appointment session around.
        _delete_session_state(session_id)

        return render_template(
            "BOOKING_FAILED",
            short_lang,
        )

    # Appointment was successfully created.
    reply = render_template(
        "CONFIRMED",
        short_lang,
        doctor=slots["doctor_name"],
        date=slots["appointment_date"],
        time=slots["appointment_time"],
    )

    # Booking is finished, so remove the temporary in-memory state.
    _delete_session_state(session_id)

    print("[Orchestrator] Appointment successfully created")

    return reply