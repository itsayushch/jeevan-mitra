from app.ivr.engine import IVREngine
from app.ivr.constants import IVRState, IVRStatus, IVRCallbackReason, PromptKey


def test_initial_state_welcome():
    res = IVREngine.get_initial_state(language="hi-IN")
    assert res.next_state == IVRState.WELCOME
    assert res.next_status == IVRStatus.ACTIVE
    assert res.prompt_key == PromptKey.WELCOME
    assert "जीवन मित्र में आपका स्वागत है" in res.prompt_text
    assert res.accepted_digits == ["1", "2"]
    assert len(res.actions) >= 1
    assert res.actions[0].prompt_key == PromptKey.WELCOME.value
    assert res.actions[0].language == "hi-IN"


def test_welcome_1_to_consent():
    res = IVREngine.transition(current_state=IVRState.WELCOME, digit="1")
    assert res.next_state == IVRState.CONSENT
    assert res.next_status == IVRStatus.ACTIVE
    assert res.prompt_key == PromptKey.CONSENT
    assert "सहमति" in res.prompt_text
    assert res.accepted_digits == ["1", "2"]
    assert res.retry_count == 0


def test_welcome_2_to_goodbye():
    res = IVREngine.transition(current_state=IVRState.WELCOME, digit="2")
    assert res.next_state == IVRState.GOODBYE
    assert res.next_status == IVRStatus.COMPLETED
    assert res.prompt_key == PromptKey.GOODBYE
    assert res.accepted_digits == []
    assert res.intent == "end_call"


def test_consent_1_accepted_to_identity():
    res = IVREngine.transition(current_state=IVRState.CONSENT, digit="1")
    assert res.next_state == IVRState.IDENTITY
    assert res.next_status == IVRStatus.ACTIVE
    assert res.prompt_key == PromptKey.IDENTITY
    assert res.intent == "grant_consent"
    assert res.accepted_digits == ["1", "0", "9"]


def test_consent_2_refused_to_goodbye():
    res = IVREngine.transition(current_state=IVRState.CONSENT, digit="2")
    assert res.next_state == IVRState.GOODBYE
    assert res.next_status == IVRStatus.TERMINATED
    assert res.prompt_key == PromptKey.CONSENT_REFUSED
    assert res.intent == "refuse_consent"
    assert res.accepted_digits == []


def test_identity_routing():
    # 1 -> main menu
    res_1 = IVREngine.transition(current_state=IVRState.IDENTITY, digit="1")
    assert res_1.next_state == IVRState.MAIN_MENU

    # 9 -> main menu
    res_9 = IVREngine.transition(current_state=IVRState.IDENTITY, digit="9")
    assert res_9.next_state == IVRState.MAIN_MENU

    # 0 -> callback request
    res_0 = IVREngine.transition(current_state=IVRState.IDENTITY, digit="0")
    assert res_0.next_state == IVRState.CALLBACK_REQUEST
    assert res_0.intent == "create_callback"
    assert res_0.callback_reason == IVRCallbackReason.GENERAL_HELP

    # # -> repeat identity
    res_hash = IVREngine.transition(current_state=IVRState.IDENTITY, digit="#")
    assert res_hash.next_state == IVRState.IDENTITY
    assert res_hash.prompt_key == PromptKey.IDENTITY


def test_main_menu_routes():
    # 1 -> training
    res_1 = IVREngine.transition(current_state=IVRState.MAIN_MENU, digit="1")
    assert res_1.next_state == IVRState.TRAINING
    assert res_1.prompt_key == PromptKey.TRAINING_MENU

    # 2 -> schemes
    res_2 = IVREngine.transition(current_state=IVRState.MAIN_MENU, digit="2")
    assert res_2.next_state == IVRState.SCHEMES
    assert res_2.prompt_key == PromptKey.SCHEME_MENU

    # 3 -> referral_status
    res_3 = IVREngine.transition(current_state=IVRState.MAIN_MENU, digit="3")
    assert res_3.next_state == IVRState.REFERRAL_STATUS
    assert res_3.prompt_key == PromptKey.REFERRAL_STATUS

    # 0 -> callback request
    res_0 = IVREngine.transition(current_state=IVRState.MAIN_MENU, digit="0")
    assert res_0.next_state == IVRState.CALLBACK_REQUEST
    assert res_0.intent == "create_callback"
    assert res_0.callback_reason == IVRCallbackReason.GENERAL_HELP

    # # -> repeat main menu
    res_hash = IVREngine.transition(current_state=IVRState.MAIN_MENU, digit="#")
    assert res_hash.next_state == IVRState.MAIN_MENU
    assert res_hash.prompt_key == PromptKey.MAIN_MENU

    # 9 -> repeat main menu
    res_9 = IVREngine.transition(current_state=IVRState.MAIN_MENU, digit="9")
    assert res_9.next_state == IVRState.MAIN_MENU


def test_training_submenu_routes():
    ctx = {
        "training_items": [
            {"id": "c1", "title": "सोलर पैनल तकनीशियन"},
            {"id": "c2", "title": "सिलाई एवं परिधान डिजाइन"},
        ]
    }
    # Press 1 -> training detail 1
    res_1 = IVREngine.transition(
        current_state=IVRState.TRAINING, digit="1", context=ctx
    )
    assert res_1.next_state == IVRState.TRAINING
    assert res_1.prompt_key == PromptKey.TRAINING_DETAIL
    assert "सोलर पैनल तकनीशियन" in res_1.prompt_text
    assert res_1.selected_item_index == 0

    # Press 0 -> callback request with TRAINING_SUPPORT reason
    res_0 = IVREngine.transition(
        current_state=IVRState.TRAINING, digit="0", context=ctx
    )
    assert res_0.next_state == IVRState.CALLBACK_REQUEST
    assert res_0.callback_reason == IVRCallbackReason.TRAINING_SUPPORT

    # Press 9 -> return to main menu
    res_9 = IVREngine.transition(
        current_state=IVRState.TRAINING, digit="9", context=ctx
    )
    assert res_9.next_state == IVRState.MAIN_MENU

    # Press # -> repeat training menu
    res_hash = IVREngine.transition(
        current_state=IVRState.TRAINING, digit="#", context=ctx
    )
    assert res_hash.next_state == IVRState.TRAINING
    assert res_hash.prompt_key == PromptKey.TRAINING_MENU


def test_schemes_submenu_routes():
    ctx = {"scheme_items": [{"id": "q1", "title": "पीएम-अजय कौशल विकास योजना"}]}
    # Press 1 -> scheme detail
    res_1 = IVREngine.transition(current_state=IVRState.SCHEMES, digit="1", context=ctx)
    assert res_1.next_state == IVRState.SCHEMES
    assert res_1.prompt_key == PromptKey.SCHEME_DETAIL
    assert "पीएम-अजय" in res_1.prompt_text
    assert "सत्यापन आवश्यक है" in res_1.prompt_text

    # Press 0 -> callback request with SCHEME_INFORMATION reason
    res_0 = IVREngine.transition(current_state=IVRState.SCHEMES, digit="0", context=ctx)
    assert res_0.next_state == IVRState.CALLBACK_REQUEST
    assert res_0.callback_reason == IVRCallbackReason.SCHEME_INFORMATION

    # Press 9 -> main menu
    res_9 = IVREngine.transition(current_state=IVRState.SCHEMES, digit="9", context=ctx)
    assert res_9.next_state == IVRState.MAIN_MENU


def test_referral_status_routes():
    # Anonymous or without referral
    res_anon = IVREngine.transition(
        current_state=IVRState.MAIN_MENU, digit="3", context={}
    )
    assert res_anon.prompt_key == PromptKey.REFERRAL_STATUS
    assert "पहचान आवश्यक है" in res_anon.prompt_text

    # Identified with summary
    res_id = IVREngine.transition(
        current_state=IVRState.MAIN_MENU,
        digit="3",
        context={"beneficiary_id": "ben_1", "referral_summary": "समीक्षा प्रगति पर है"},
    )
    assert res_id.prompt_key == PromptKey.REFERRAL_STATUS_IDENTIFIED
    assert "समीक्षा प्रगति पर है" in res_id.prompt_text

    # Press 0 from referral status -> callback request with REFERRAL_STATUS reason
    res_cb = IVREngine.transition(current_state=IVRState.REFERRAL_STATUS, digit="0")
    assert res_cb.next_state == IVRState.CALLBACK_REQUEST
    assert res_cb.callback_reason == IVRCallbackReason.REFERRAL_STATUS


def test_invalid_input_retry_and_max_retries():
    # Attempt 1: First invalid input returns INVALID_INPUT prompt and retry_count=1
    res_1 = IVREngine.transition(
        current_state=IVRState.MAIN_MENU,
        digit="5",
        invalid_attempt_count=0,
        max_retries=2,
    )
    assert res_1.next_state == IVRState.MAIN_MENU
    assert res_1.prompt_key == PromptKey.INVALID_INPUT
    assert "अमान्य इनपुट" in res_1.prompt_text
    assert res_1.retry_count == 1
    assert res_1.intent == "invalid_input"

    # Attempt 2: Second invalid input hits max retries -> transitions to ERROR_RETRY
    res_2 = IVREngine.transition(
        current_state=IVRState.MAIN_MENU,
        digit="8",
        invalid_attempt_count=1,
        max_retries=2,
    )
    assert res_2.next_state == IVRState.ERROR_RETRY
    assert res_2.prompt_key == PromptKey.MAX_RETRIES
    assert "अमान्य विकल्प" in res_2.prompt_text
    assert res_2.retry_count == 2
    assert res_2.accepted_digits == ["0", "2"]

    # From ERROR_RETRY: 0 -> callback request
    res_cb = IVREngine.transition(current_state=IVRState.ERROR_RETRY, digit="0")
    assert res_cb.next_state == IVRState.CALLBACK_REQUEST

    # From ERROR_RETRY: 2 -> goodbye
    res_bye = IVREngine.transition(current_state=IVRState.ERROR_RETRY, digit="2")
    assert res_bye.next_state == IVRState.GOODBYE
    assert res_bye.next_status == IVRStatus.COMPLETED


def test_expired_session_handling():
    res = IVREngine.transition(
        current_state=IVRState.MAIN_MENU, digit="1", is_expired=True
    )
    assert res.next_state == IVRState.EXPIRED
    assert res.next_status == IVRStatus.EXPIRED
    assert res.prompt_key == PromptKey.SESSION_EXPIRED
    assert res.accepted_digits == []


def test_goodbye_completed_terminal_state():
    res = IVREngine.transition(current_state=IVRState.GOODBYE, digit="1")
    assert res.next_state == IVRState.GOODBYE
    assert res.next_status == IVRStatus.COMPLETED
    assert res.prompt_key == PromptKey.GOODBYE
    assert res.accepted_digits == []
