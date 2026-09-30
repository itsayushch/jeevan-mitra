from enum import Enum
from typing import Optional, Set
from fastapi import Request

class SupportedLocale(str, Enum):
    EN = "en"
    HI = "hi"
    BN = "bn"
    MR = "mr"
    TA = "ta"

ENABLED_LOCALES: Set[SupportedLocale] = {SupportedLocale.EN, SupportedLocale.HI}
DEFAULT_LOCALE = SupportedLocale.EN

def is_valid_locale(val: Optional[str]) -> bool:
    if not val:
        return False
    clean = val.strip().lower()
    return clean in [e.value for e in SupportedLocale]

def is_enabled_locale(val: Optional[str]) -> bool:
    if not val:
        return False
    clean = val.strip().lower()
    return clean in [e.value for e in ENABLED_LOCALES]

def parse_locale(val: Optional[str]) -> Optional[SupportedLocale]:
    if not val:
        return None
    clean = val.strip().lower()
    # Handle language-region tags like hi-IN, en-US
    primary = clean.split("-")[0].split("_")[0]
    for e in SupportedLocale:
        if e.value == clean or e.value == primary:
            return e
    return None

def resolve_locale(
    request: Optional[Request] = None,
    explicit_locale: Optional[str] = None,
    actor_preferred_language: Optional[str] = None,
    require_enabled: bool = True,
    accept_language: Optional[str] = None,
    preferred_language: Optional[str] = None
) -> SupportedLocale:
    """
    Standardized locale resolution order:
    1. Explicit request field/query if valid
    2. Accept-Language header if valid
    3. Authenticated user preferred_language
    4. English fallback ('en')
    """
    # 1. Explicit request parameter
    if explicit_locale:
        parsed = parse_locale(explicit_locale)
        if parsed and (not require_enabled or parsed in ENABLED_LOCALES):
            return parsed

    # 2. Accept-Language header
    header_val = accept_language or (request.headers.get("accept-language") if request else None)
    if header_val:
        tokens = [t.split(";")[0].strip() for t in header_val.split(",")]
        for tok in tokens:
            parsed = parse_locale(tok)
            if parsed and (not require_enabled or parsed in ENABLED_LOCALES):
                return parsed

    # 3. Authenticated user's preferred_language
    pref = preferred_language or actor_preferred_language
    if pref:
        parsed = parse_locale(pref)
        if parsed and (not require_enabled or parsed in ENABLED_LOCALES):
            return parsed

    # 4. English fallback
    return DEFAULT_LOCALE
