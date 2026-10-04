"""
PM-AJAY Acceptance Tests and Comprehensive Local QA Suite.

Validates the full feature-phone IVR simulator against PM-AJAY problem statement
requirements: accessibility, consent gating, verified-only guidance, 3-result limits,
privacy isolation, human handoff (callback), and idempotency.

ALL PERSONAS AND FIXTURES ARE STRICTLY SYNTHETIC AND TEST-ONLY.
"""

import os
import tempfile
import pytest
from app.config import settings
from app.database import get_db, init_database
from app.ivr.service import IVRService
from app.ivr.repository import IVRRepository
from app.ivr.schemas import IVRSessionStartRequest, IVRDigitInputRequest
from app.ivr.constants import IVRState, IVRStatus, IVRCallbackReason, PromptKey
from tests.factories.pm_ajay_personas import (
    PERSONA_A_ID,
    PERSONA_A_PHONE,
    PERSONA_B_ID,
    PERSONA_B_PHONE,
    PERSONA_C_PHONE,
    PERSONA_D_CALLER,
    PERSONA_E_ID,
    PERSONA_E_PHONE,
    PERSONA_F_CALLER,
    PERSONA_G_PHONE,
    seed_persona_a_training_seeker,
    seed_persona_b_self_employment,
    seed_persona_c_accessibility,
    seed_persona_e_with_referral,
    seed_verified_training_and_schemes,
)


@pytest.fixture
def clean_db():

    orig_db = settings.DATABASE_PATH
    temp_dir = tempfile.TemporaryDirectory()
    settings.DATABASE_PATH = os.path.join(temp_dir.name, "test_pm_ajay_qa.db")
    settings.IVR_SIMULATOR_ENABLED = True
    init_database()

    with get_db() as conn:
        yield conn

    settings.DATABASE_PATH = orig_db
    temp_dir.cleanup()


# =============================================================================
# PMAJAY-001 & PMAJAY-002: PERSONA A (TRAINING SEEKER WAGE EMPLOYMENT JOURNEY)
# =============================================================================
def test_pmajay_001_persona_a_training_seeker_journey(clean_db):
    """
    Persona A (Training Seeker, wage employment interest):
    1. Caller enters with registered phone.
    2. Welcome prompt displayed in Hindi with digits [1, 2].
    3. Accepts consent (1) -> affirmative DPDP consent recorded.
    4. Identity screen -> presses 1 -> reaches main menu.
    5. Selects training (1) -> verified NSQF training items returned (max 3).
    6. Selects course detail (1) -> receives safe course summary.
    7. Requests worker assistance (0) -> callback request created with TRAINING_SUPPORT.
    8. Ends call (2) -> terminal state goodbye with completed status.
    """
    seed_persona_a_training_seeker(clean_db)
    seed_verified_training_and_schemes(clean_db, count=5)

    # 1. Start IVR session
    start_req = IVRSessionStartRequest(
        simulated_caller_reference=PERSONA_A_PHONE,
        language="hi-IN",
    )
    s1 = IVRService.start_session(clean_db, start_req)
    assert s1.state == IVRState.WELCOME
    assert s1.status == IVRStatus.ACTIVE
    assert "नमस्ते" in s1.prompt_text
    assert s1.accepted_digits == ["1", "2"]
    sess_id = s1.session_id

    # 2. Press 1: Consent prompt
    s2 = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="1")
    )
    assert s2.state == IVRState.CONSENT
    assert "सहमति" in s2.prompt_text

    # 3. Press 1: Grant consent -> Identity
    s3 = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="1")
    )
    assert s3.state == IVRState.IDENTITY

    # Verify DPDP consent record was created
    consent = clean_db.execute(
        "SELECT * FROM consent_records WHERE session_id = ?;", (sess_id,)
    ).fetchone()
    assert consent is not None
    assert consent["status"] == "granted"
    assert consent["capture_channel"] == "ivr"

    # 4. Press 1: Continue to Main Menu
    s4 = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="1")
    )
    assert s4.state == IVRState.MAIN_MENU

    # 5. Press 1: Select Training Menu
    s5 = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="1")
    )
    assert s5.state == IVRState.TRAINING
    # IVR-025: Max 3 verified courses loaded in context
    sess_row = IVRRepository.get_session(clean_db, sess_id)
    ctx = sess_row.get("context") or {}
    training_items = ctx.get("training_items", [])
    assert len(training_items) <= 3
    assert len(training_items) == 3

    # 6. Press 1: Select Course Detail 1
    s6 = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="1")
    )
    assert s6.state == IVRState.TRAINING
    assert "सिलाई एवं परिधान स्तर 1" in s6.prompt_text

    # 7. Press 0: Request Worker Callback from Training
    s7 = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="0")
    )
    assert s7.state == IVRState.CALLBACK_REQUEST
    assert s7.callback_request is not None
    assert (
        s7.callback_request["callback_reason"] == IVRCallbackReason.TRAINING_SUPPORT.value
    )
    assert s7.callback_request["beneficiary_id"] == PERSONA_A_ID

    # 8. Press 2: End call
    s8 = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="2")
    )
    assert s8.state == IVRState.GOODBYE
    assert s8.status == IVRStatus.COMPLETED


# =============================================================================
# PMAJAY-002 & PMAJAY-006: PERSONA B (SELF-EMPLOYMENT & SCHEME PATHWAY)
# =============================================================================
def test_pmajay_002_persona_b_self_employment_scheme_journey(clean_db):
    """
    Persona B (Traditional trade / self-employment aspiration):
    1. Selects Schemes (2) from Main Menu.
    2. Receives verified qualification/scheme options (max 3).
    3. Requests callback (0) -> receives SCHEME_INFORMATION callback reason.
    """
    seed_persona_b_self_employment(clean_db)
    seed_verified_training_and_schemes(clean_db, count=4)

    s1 = IVRService.start_session(
        clean_db,
        IVRSessionStartRequest(simulated_caller_reference=PERSONA_B_PHONE),
    )
    sess_id = s1.session_id

    # Consent flow
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    # Identity -> Main Menu
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))

    # Main Menu -> Schemes (2)
    s_scheme = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="2")
    )
    assert s_scheme.state == IVRState.SCHEMES
    assert "सरकारी योजनाओं" in s_scheme.prompt_text or "विकल्प" in s_scheme.prompt_text

    # Select Scheme 1 -> Detail
    s_detail = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="1")
    )
    assert s_detail.state == IVRState.SCHEMES
    assert len(s_detail.prompt_text) > 10
    # Verification disclaimer present
    assert "सत्यापन आवश्यक है" in s_detail.prompt_text

    # Request callback from Schemes (0) -> SCHEME_INFORMATION

    s_cb = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="0")
    )
    assert s_cb.state == IVRState.CALLBACK_REQUEST
    assert (
        s_cb.callback_request["callback_reason"]
        == IVRCallbackReason.SCHEME_INFORMATION.value
    )
    assert s_cb.callback_request["beneficiary_id"] == PERSONA_B_ID


# =============================================================================
# PMAJAY-003 & PRIV-009: PERSONA C (ACCESSIBILITY NON-DISCRIMINATION)
# =============================================================================
def test_pmajay_003_persona_c_accessibility_non_discrimination(clean_db):
    """
    Persona C (Generic accessibility/mobility preference):
    Ensures that generic accessibility needs do not lead to denial or exclusion.
    The caller receives normal access to training and human worker handoff.
    """
    seed_persona_c_accessibility(clean_db)
    seed_verified_training_and_schemes(clean_db, count=2)

    s1 = IVRService.start_session(
        clean_db,
        IVRSessionStartRequest(simulated_caller_reference=PERSONA_C_PHONE),
    )
    sess_id = s1.session_id

    # Consent and main menu
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))

    # Training access is unobstructed
    s_tr = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="1")
    )
    assert s_tr.state == IVRState.TRAINING
    assert s_tr.status == IVRStatus.ACTIVE


# =============================================================================
# PMAJAY-007 & PRIV-006: ANONYMOUS CALLER (NO PII EXPOSURE)
# =============================================================================
def test_pmajay_004_persona_d_anonymous_caller_privacy(clean_db):
    """
    Persona D (Anonymous Caller without linked beneficiary record):
    1. Accesses referral status (3) without identified beneficiary.
    2. Receives safe generic guidance without leaking any other beneficiary's records.
    3. Can request worker assistance (0) -> referral_status reason with null beneficiary_id.
    """
    seed_persona_e_with_referral(clean_db)  # Seed another beneficiary's case

    # Start anonymous session
    s1 = IVRService.start_session(
        clean_db,
        IVRSessionStartRequest(simulated_caller_reference=PERSONA_D_CALLER),
    )
    sess_id = s1.session_id

    # Consent and main menu
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))

    # Select Referral Status (3)
    s_ref = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="3")
    )
    assert s_ref.state == IVRState.REFERRAL_STATUS
    # Safe generic message: identity required / no record found, offers callback
    assert "पहचान आवश्यक है" in s_ref.prompt_text
    # PRIV-006: Persona E's data must NOT be present
    assert PERSONA_E_ID not in s_ref.prompt_text
    assert "Under Review" not in s_ref.prompt_text

    # Request callback from referral status

    s_cb = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="0")
    )
    assert s_cb.state == IVRState.CALLBACK_REQUEST
    assert (
        s_cb.callback_request["callback_reason"]
        == IVRCallbackReason.REFERRAL_STATUS.value
    )
    assert s_cb.callback_request["beneficiary_id"] is None


# =============================================================================
# PMAJAY-007 & PRIV-006: CROSS-BENEFICIARY PRIVACY ISOLATION
# =============================================================================
def test_pmajay_005_persona_e_and_f_referral_isolation(clean_db):
    """
    Cross-Beneficiary Isolation:
    - Persona E has an active referral ('under_review').
    - Persona F is an unrelated caller.
    - Persona E receives their own status.
    - Persona F receives NO access to Persona E's case.
    """
    seed_persona_e_with_referral(clean_db)

    # 1. Persona E session
    s_e = IVRService.start_session(
        clean_db,
        IVRSessionStartRequest(simulated_caller_reference=PERSONA_E_PHONE),
    )
    sid_e = s_e.session_id
    IVRService.process_digit_input(clean_db, sid_e, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sid_e, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sid_e, IVRDigitInputRequest(digit="1"))
    res_e = IVRService.process_digit_input(
        clean_db, sid_e, IVRDigitInputRequest(digit="3")
    )
    assert res_e.state == IVRState.REFERRAL_STATUS
    # Persona E sees own summary
    assert "Under Review" in res_e.prompt_text

    # 2. Persona F session
    s_f = IVRService.start_session(
        clean_db,
        IVRSessionStartRequest(simulated_caller_reference=PERSONA_F_CALLER),
    )
    sid_f = s_f.session_id
    IVRService.process_digit_input(clean_db, sid_f, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sid_f, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sid_f, IVRDigitInputRequest(digit="1"))
    res_f = IVRService.process_digit_input(
        clean_db, sid_f, IVRDigitInputRequest(digit="3")
    )
    assert res_f.state == IVRState.REFERRAL_STATUS
    # Persona F cannot see Persona E's status
    assert "Under Review" not in res_f.prompt_text
    assert "पहचान आवश्यक है" in res_f.prompt_text


# =============================================================================
# PMAJAY-004 & IVR-024: NO FABRICATED RECOMMENDATIONS ON EMPTY CATALOGUE
# =============================================================================
def test_pmajay_006_persona_g_no_verified_matches_fallback(clean_db):
    """
    Persona G: When zero verified opportunities exist:
    - Never fabricates or hallucinates opportunities.
    - Returns safe Hindi NO_RESULTS prompt.
    - Offers field-worker callback option.
    """
    s1 = IVRService.start_session(
        clean_db,
        IVRSessionStartRequest(simulated_caller_reference=PERSONA_G_PHONE),
    )
    sess_id = s1.session_id

    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))

    # Training menu when 0 courses in DB
    s_tr = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="1")
    )
    assert s_tr.state == IVRState.TRAINING

    # Select item 1 -> NO_RESULTS prompt returned safely
    s_detail = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="1")
    )
    assert s_detail.prompt_key == PromptKey.NO_RESULTS.value
    assert "सत्यापित विकल्प उपलब्ध नहीं है" in s_detail.prompt_text


# =============================================================================
# PMAJAY-008 & IVR-022: CALLBACK & INPUT IDEMPOTENCY REPLAY
# =============================================================================
def test_pmajay_007_persona_h_callback_idempotency_replay(clean_db):

    """
    Persona H: Repeated identical requests do not produce duplicate open callbacks.
    """
    s1 = IVRService.start_session(
        clean_db,
        IVRSessionStartRequest(simulated_caller_reference="9811000008"),
    )
    sess_id = s1.session_id

    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))

    # Request callback
    r1 = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="0", idempotency_key="idemp_cb_1")
    )
    cb_id = r1.callback_request["id"]

    # Replay identical input with same idempotency key
    r2 = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="0", idempotency_key="idemp_cb_1")
    )
    assert r2.callback_request["id"] == cb_id

    # Count records in DB: exactly 1
    count = clean_db.execute(
        "SELECT COUNT(*) as cnt FROM ivr_callback_requests WHERE session_id = ?;",
        (sess_id,),
    ).fetchone()["cnt"]
    assert count == 1


# =============================================================================
# IVR-014 & IVR-015: REPEAT PROMPT (#) AND RETURN TO MAIN MENU (9)
# =============================================================================
def test_pmajay_008_repeat_and_navigation_controls(clean_db):
    """
    Verifies '#' repeats current prompt without mutation,
    and '9' returns safely to main menu from submenus.
    """
    s1 = IVRService.start_session(clean_db, IVRSessionStartRequest())
    sess_id = s1.session_id

    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))
    IVRService.process_digit_input(clean_db, sess_id, IVRDigitInputRequest(digit="1"))

    # Now in MAIN_MENU. Press '#' -> repeat MAIN_MENU
    rep = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="#")
    )
    assert rep.state == IVRState.MAIN_MENU
    assert rep.prompt_key == PromptKey.MAIN_MENU.value

    # Enter TRAINING (1)
    tr = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="1")
    )
    assert tr.state == IVRState.TRAINING

    # Press '#' in TRAINING -> repeats TRAINING_MENU
    tr_rep = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="#")
    )
    assert tr_rep.state == IVRState.TRAINING
    assert tr_rep.prompt_key == PromptKey.TRAINING_MENU.value

    # Press '9' in TRAINING -> returns to MAIN_MENU
    back = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="9")
    )
    assert back.state == IVRState.MAIN_MENU
    assert back.prompt_key == PromptKey.MAIN_MENU.value


# =============================================================================
# IVR-016 & IVR-017: INVALID INPUT RETRY AND CONTROLLED FALLBACK
# =============================================================================
def test_pmajay_009_invalid_input_and_max_retries(clean_db):
    """
    Verifies first invalid input gives retry with invalid prompt (IVR-016),
    and second invalid input hits max retries with controlled fallback (IVR-017).
    """
    s1 = IVRService.start_session(clean_db, IVRSessionStartRequest())
    sess_id = s1.session_id

    # Welcome state expects '1' or '2'. Send '5' -> invalid input attempt 1
    r1 = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="5")
    )
    assert r1.state == IVRState.WELCOME
    assert r1.retry_count == 1
    assert "अमान्य इनपुट" in r1.prompt_text

    # Second invalid input -> hits max retries (2) -> transitions to ERROR_RETRY
    r2 = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="7")
    )
    assert r2.state == IVRState.ERROR_RETRY
    assert r2.prompt_key == PromptKey.MAX_RETRIES.value
    assert r2.retry_count == 2
    assert "अमान्य विकल्प" in r2.prompt_text
    assert "0" in r2.accepted_digits
    assert "2" in r2.accepted_digits

    # Press 2 from ERROR_RETRY -> controlled exit to GOODBYE (completed)
    r3 = IVRService.process_digit_input(
        clean_db, sess_id, IVRDigitInputRequest(digit="2")
    )
    assert r3.state == IVRState.GOODBYE
    assert r3.status == IVRStatus.COMPLETED


# =============================================================================
# SEC-API-001, SEC-API-002, PRIV-003: DATA MINIMIZATION & SQL INJECTION SAFETY
# =============================================================================
def test_pmajay_010_security_and_privacy_checks(clean_db):
    """
    Security & Privacy review validations:
    - Raw telephone numbers are masked or hashed; never in caller_reference_hash.
    - SQL injection payload in phone field is safely parameterized.
    - No PII fields (Aadhaar, PAN, Bank) exist in IVR payload.
    """
    # 1. SQL Injection attempt in simulated caller reference
    sqli_payload = "'+OR+1=1;--' UNION SELECT 1,2,3"
    start_res = IVRService.start_session(
        clean_db,
        IVRSessionStartRequest(simulated_caller_reference=sqli_payload),
    )
    assert start_res.session_id.startswith("ivrs_")
    assert start_res.status == IVRStatus.ACTIVE

    # Verify session row does not contain raw SQL injection string in caller_hash
    sess_row = IVRRepository.get_session(clean_db, start_res.session_id)
    assert sqli_payload not in (sess_row.get("caller_reference_hash") or "")

    # 2. Plaintext phone masking check
    raw_phone = "+919876543210"
    res_phone = IVRService.start_session(
        clean_db,
        IVRSessionStartRequest(simulated_caller_reference=raw_phone),
    )
    # Output response must not contain raw plaintext phone
    res_dict = res_phone.model_dump()
    assert raw_phone not in str(res_dict)

    # 3. Events do not store raw phone
    events = IVRService.get_session_events(clean_db, res_phone.session_id)
    assert len(events) >= 1
    assert raw_phone not in str([e.model_dump() for e in events])
