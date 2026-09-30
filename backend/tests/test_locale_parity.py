import json
from pathlib import Path
import pytest

LOCALES_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "locales"

def get_flattened_keys(d, prefix=""):
    keys = set()
    for k, v in d.items():
        curr_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(get_flattened_keys(v, curr_key))
        else:
            keys.add(curr_key)
    return keys

def test_canonical_locale_file_exists():
    canonical_file = LOCALES_DIR / "en.json"
    assert canonical_file.exists(), "frontend/src/locales/en.json must exist"

def test_locale_key_parity():
    canonical_file = LOCALES_DIR / "en.json"
    assert canonical_file.exists(), f"Canonical file not found at {canonical_file}"
    
    with open(canonical_file, "r", encoding="utf-8") as f:
        canonical_data = json.load(f)
    canonical_keys = get_flattened_keys(canonical_data)
    assert len(canonical_keys) > 0, "Canonical en.json must not be empty"

    # Enabled and registered locales
    locales_to_test = ["hi", "bn", "mr", "ta"]

    for loc in locales_to_test:
        loc_file = LOCALES_DIR / f"{loc}.json"
        assert loc_file.exists(), f"Locale file {loc}.json must exist"
        
        with open(loc_file, "r", encoding="utf-8") as f:
            loc_data = json.load(f)
        loc_keys = get_flattened_keys(loc_data)

        missing_keys = canonical_keys - loc_keys
        extra_keys = loc_keys - canonical_keys

        assert not missing_keys, f"Locale '{loc}' is missing keys present in canonical en.json: {missing_keys}"
        assert not extra_keys, f"Locale '{loc}' has extra keys not present in canonical en.json: {extra_keys}"
        assert loc_keys == canonical_keys, f"Locale '{loc}' keys do not match canonical en.json keys"
