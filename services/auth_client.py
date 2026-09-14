"""
DEMO AUTH -- TEMPORARY.

This client normally wraps Team C's authentication endpoint
(POST /api/v1/auth/login). For this standalone deployment/testing phase we
are NOT depending on Team C's database/backend, so login is backed by
services.demo_store instead: a valid-looking 10-digit Indian phone number
is accepted and self-registered in memory, with no password, no OTP, and no
real database anywhere in the flow.

The function signature and exceptions below are kept identical to the
original Team C-backed client, so services/gateway/main.py did not need to
change. To restore the real Team C integration later, swap the body of
login() back to an HTTP call to TEAM_C_BASE_URL/api/v1/auth/login (see git
history for the original implementation).
"""
from services.demo_store import (
    demo_login,
    PhoneNotRegistered,
    InvalidPhoneNumber,
)

__all__ = ["login", "PhoneNotRegistered", "InvalidPhoneNumber"]


def login(phone_no: str) -> dict:
    """
    DEMO AUTH -- TEMPORARY.

    Sign a phone number in, registering it in memory if it hasn't been seen
    in this process before.

    Returns the account dict: {'auth_id', 'phone_no', 'is_new'}, where
    is_new is True when this call created the account.

    Raises InvalidPhoneNumber for a malformed number. PhoneNotRegistered is
    kept for interface parity with the real Team C client but will not fire
    in this demo flow, since unknown numbers are self-registered rather than
    rejected.
    """
    return demo_login(phone_no)
