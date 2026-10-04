import os
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from app.config import settings
from app.database import get_db, init_database
from app.ivr.service import IVRService
from app.ivr.repository import IVRRepository
from app.ivr.schemas import IVRSessionStartRequest, IVRDigitInputRequest
from app.ivr.constants import IVRState, IVRStatus, IVRCallbackReason


@pytest.fixture
def db_conn():
    orig_db = settings.DATABASE_PATH
    temp_dir = tempfile.TemporaryDirectory()
    settings.DATABASE_PATH = os.path.join(temp_dir.name, "test_ivr_service.db")
    init_database()

    with get_db() as conn:
        yield conn

    settings.DATABASE_PATH = orig_db
    temp_dir.cleanup()


def test_start_session_persists_active_session(db_conn):
    req = IVRSessionStartRequest(
        simulated_caller_reference="+919876543210",
        language="hi-IN",
        idempotency_key="idemp_start_01",
    )
    res = IVRService.start_session(db_conn, req)

    assert res.session_id.startswith("ivrs_")
    assert res.state == IVRState.WELCOME
    assert res.status == IVRStatus.ACTIVE
    assert "नमस्ते" in res.prompt_text

    # Verify session persisted in DB
    session = IVRRepository.get_session(db_conn, res.session_id)
    assert session is not None
    assert session["current_state"] == "welcome"
    assert session["status"] == "active"
    # Verify no raw phone stored in caller_reference_hash
    assert "+919876543210" not in (session.get("caller_reference_hash") or "")


def test_state_transition_persists_event(db_conn):
    start_req = IVRSessionStartRequest()
    start_res = IVRService.start_session(db_conn, start_req)
    session_id = start_res.session_id

    # Enter '1' -> should transition to consent
    input_req = IVRDigitInputRequest(digit="1", idempotency_key="step_1")
    input_res = IVRService.process_digit_input(db_conn, session_id, input_req)

    assert input_res.state == IVRState.CONSENT
    assert input_res.previous_state == IVRState.WELCOME
    assert "सहमति" in input_res.prompt_text

    # Verify event history has both session_started and state_transitioned
    events = IVRService.get_session_events(db_conn, session_id)
    assert len(events) >= 2
    assert events[0].event_type == "session_started"
    assert events[1].event_type == "state_transitioned"
    assert events[1].digit == "1"


def test_consent_grant_creates_consent_record(db_conn):
    start_res = IVRService.start_session(db_conn, IVRSessionStartRequest())
    sess_id = start_res.session_id

    # 1 -> consent
    IVRService.process_digit_input(db_conn, sess_id, IVRDigitInputRequest(digit="1"))
    # 1 -> identity (grants consent)
    res = IVRService.process_digit_input(
        db_conn, sess_id, IVRDigitInputRequest(digit="1")
    )

    assert res.state == IVRState.IDENTITY

    # Check that a consent_record was created for this IVR session
    c_row = db_conn.execute(
        "SELECT * FROM consent_records WHERE session_id = ?;", (sess_id,)
    ).fetchone()
    assert c_row is not None
    assert c_row["capture_channel"] == "ivr"
    assert c_row["status"] == "granted"


def test_input_idempotency_prevents_duplicate_work(db_conn):
    start_res = IVRService.start_session(db_conn, IVRSessionStartRequest())
    sess_id = start_res.session_id

    # First call with idempotency key
    input_req = IVRDigitInputRequest(digit="1", idempotency_key="unique_key_100")
    res1 = IVRService.process_digit_input(db_conn, sess_id, input_req)
    assert res1.state == IVRState.CONSENT

    events_count_before = len(IVRService.get_session_events(db_conn, sess_id))

    # Replayed call with SAME idempotency key
    res2 = IVRService.process_digit_input(db_conn, sess_id, input_req)
    assert res2.state == IVRState.CONSENT
    assert res2.prompt_text == res1.prompt_text

    # Ensure no new event was appended
    events_count_after = len(IVRService.get_session_events(db_conn, sess_id))
    assert events_count_after == events_count_before


def test_callback_request_idempotency(db_conn):
    start_res = IVRService.start_session(db_conn, IVRSessionStartRequest())
    sess_id = start_res.session_id

    # Welcome -> 1 -> Consent -> 1 -> Identity
    IVRService.process_digit_input(db_conn, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(db_conn, sess_id, IVRDigitInputRequest(digit="1"))

    # Identity -> 0 -> Callback request
    res1 = IVRService.process_digit_input(
        db_conn, sess_id, IVRDigitInputRequest(digit="0")
    )
    assert res1.state == IVRState.CALLBACK_REQUEST
    assert res1.callback_request is not None
    first_cb_id = res1.callback_request["id"]
    assert (
        res1.callback_request["callback_reason"] == IVRCallbackReason.GENERAL_HELP.value
    )

    # From Callback request -> 9 -> Main menu
    IVRService.process_digit_input(db_conn, sess_id, IVRDigitInputRequest(digit="9"))

    # From Main menu -> 0 -> Callback request again
    res2 = IVRService.process_digit_input(
        db_conn, sess_id, IVRDigitInputRequest(digit="0")
    )
    assert res2.state == IVRState.CALLBACK_REQUEST
    assert res2.callback_request is not None
    # Must reuse the same callback request record, not create a duplicate!
    assert res2.callback_request["id"] == first_cb_id

    # Check in DB that only 1 record exists for this session
    cb_rows = db_conn.execute(
        "SELECT COUNT(*) as cnt FROM ivr_callback_requests WHERE session_id = ?;",
        (sess_id,),
    ).fetchone()
    assert cb_rows["cnt"] == 1


def test_automatic_session_expiry(db_conn):
    start_res = IVRService.start_session(db_conn, IVRSessionStartRequest())
    sess_id = start_res.session_id

    # Backdate expires_at in DB to simulate timeout
    past_iso = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    db_conn.execute(
        "UPDATE ivr_sessions SET expires_at = ? WHERE id = ?;", (past_iso, sess_id)
    )

    # Next input should detect expiry and not allow state mutation
    res = IVRService.process_digit_input(
        db_conn, sess_id, IVRDigitInputRequest(digit="1")
    )
    assert res.state == IVRState.EXPIRED
    assert res.status == IVRStatus.EXPIRED
    assert "सत्र समाप्त" in res.prompt_text


def test_force_expire_session(db_conn):
    start_res = IVRService.start_session(db_conn, IVRSessionStartRequest())
    sess_id = start_res.session_id

    expired_res = IVRService.force_expire_session(db_conn, sess_id)
    assert expired_res.state == IVRState.EXPIRED
    assert expired_res.status == IVRStatus.EXPIRED

    session = IVRRepository.get_session(db_conn, sess_id)
    assert session["status"] == "expired"


def test_registered_phone_lookup(db_conn):
    # Insert test beneficiary with phone
    ben_id = "ben_test_phone_01"
    now_iso = datetime.now(timezone.utc).isoformat()
    db_conn.execute(
        """
        INSERT INTO beneficiaries (id, name, phone, district, block, created_at, updated_at)
        VALUES (?, 'Ramesh Kumar', '9811223344', 'Moradabad', 'Chhajlet', ?, ?);
    """,
        (ben_id, now_iso, now_iso),
    )

    # Start session with that phone
    res = IVRService.start_session(
        db_conn, IVRSessionStartRequest(simulated_caller_reference="9811223344")
    )
    sess = IVRRepository.get_session(db_conn, res.session_id)
    assert sess["beneficiary_id"] == ben_id


def test_consent_refusal_terminates_session(db_conn):
    start_res = IVRService.start_session(db_conn, IVRSessionStartRequest())
    sess_id = start_res.session_id

    # Welcome -> 1 -> Consent
    r1 = IVRService.process_digit_input(
        db_conn, sess_id, IVRDigitInputRequest(digit="1")
    )
    assert r1.state == IVRState.CONSENT

    # Consent -> 2 -> Refusal -> Goodbye (terminated)
    r2 = IVRService.process_digit_input(
        db_conn, sess_id, IVRDigitInputRequest(digit="2")
    )
    assert r2.state == IVRState.GOODBYE
    assert r2.status == IVRStatus.TERMINATED
    assert "सहमति" in r2.prompt_text or "धन्यवाद" in r2.prompt_text

    # Session in DB reflects terminated
    session = IVRRepository.get_session(db_conn, sess_id)
    assert session["current_state"] == "goodbye"
    assert session["status"] == "terminated"


def test_mock_row_mapping_protocol():
    """
    Verifies MockRow mapping behavior:
    1. Integer index access via tuple
    2. String key access via mapping
    3. .get(key, default)
    4. dict(row) conversion via __iter__
    """
    from app.db.session import MockRow

    mapping = {"id": "c1", "title": "Tailoring", "sector": "Apparel"}
    tuple_row = ("c1", "Tailoring", "Apparel")
    row = MockRow(mapping, tuple_row)

    # 1. Index access
    assert row[0] == "c1"
    assert row[1] == "Tailoring"

    # 2. String key access
    assert row["id"] == "c1"
    assert row["title"] == "Tailoring"

    # 3. .get() access with default
    assert row.get("sector") == "Apparel"
    assert row.get("nonexistent", "default_val") == "default_val"
    assert row.get("missing") is None

    # 4. dict(row) conversion
    row_dict = dict(row)
    assert row_dict == mapping
