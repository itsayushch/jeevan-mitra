"""
PM-AJAY Synthetic Personas and Test Data Factories for Local Testing.

ALL DATA IN THIS MODULE IS STRICTLY SYNTHETIC AND TEST-ONLY.
NO REAL NAMES, PII, AADHAAR, PAN, BANK ACCOUNTS, OR LIVE PHONE NUMBERS.
"""

from datetime import datetime, timezone
from typing import Dict, Any


# Synthetic test persona identifiers

PERSONA_A_ID = "TEST_BENEFICIARY_A"
PERSONA_A_PHONE = "9811000001"

PERSONA_B_ID = "TEST_BENEFICIARY_B"
PERSONA_B_PHONE = "9811000002"

PERSONA_C_ID = "TEST_BENEFICIARY_C"
PERSONA_C_PHONE = "9811000003"

PERSONA_D_CALLER = "9811000004"  # Anonymous, no beneficiary record

PERSONA_E_ID = "TEST_BENEFICIARY_E"
PERSONA_E_PHONE = "9811000005"

PERSONA_F_CALLER = "9811000006"  # Mismatched/unauthorized caller

PERSONA_G_ID = "TEST_BENEFICIARY_G"
PERSONA_G_PHONE = "9811000007"  # No matching opportunities

PERSONA_H_ID = "TEST_BENEFICIARY_H"
PERSONA_H_PHONE = "9811000008"  # Replay/callback idempotency


def seed_persona_a_training_seeker(conn) -> Dict[str, Any]:
    """
    Persona A: Training Seeker
    - Hindi language preference
    - Basic school education (8th/10th)
    - Interest: tailoring/retail/digital services
    - Preference: Wage employment
    - District: Moradabad, Block: Chhajlet
    """
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT OR REPLACE INTO beneficiaries (
            id, name, phone, district, block, created_at, updated_at
        ) VALUES (?, 'Test Beneficiary A', ?, 'Moradabad', 'Chhajlet', ?, ?);
        """,
        (PERSONA_A_ID, PERSONA_A_PHONE, now, now),
    )
    return {
        "id": PERSONA_A_ID,
        "name": "Test Beneficiary A",
        "phone": PERSONA_A_PHONE,
        "district": "Moradabad",
        "block": "Chhajlet",
        "persona_type": "training_seeker",
    }


def seed_persona_b_self_employment(conn) -> Dict[str, Any]:
    """
    Persona B: Traditional Occupation / Self-Employment
    - Hindi preference
    - Family occupation: handicraft/trade support
    - Preference: Self-employment / micro-enterprise
    - District: Moradabad, Block: Dilari
    """
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT OR REPLACE INTO beneficiaries (
            id, name, phone, district, block, created_at, updated_at
        ) VALUES (?, 'Test Beneficiary B', ?, 'Moradabad', 'Dilari', ?, ?);
        """,
        (PERSONA_B_ID, PERSONA_B_PHONE, now, now),
    )
    return {
        "id": PERSONA_B_ID,
        "name": "Test Beneficiary B",
        "phone": PERSONA_B_PHONE,
        "district": "Moradabad",
        "block": "Dilari",
        "persona_type": "self_employment",
    }


def seed_persona_c_accessibility(conn) -> Dict[str, Any]:
    """
    Persona C: Accessibility / Generic Mobility Preference
    - Hindi preference
    - Generic accessibility preference (non-medical attribute)
    - Preference: Local/home-accessible work
    - Must NOT be discriminatorily excluded or denied
    """
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT OR REPLACE INTO beneficiaries (
            id, name, phone, district, block, created_at, updated_at
        ) VALUES (?, 'Test Beneficiary C', ?, 'Moradabad', 'Chhajlet', ?, ?);
        """,
        (PERSONA_C_ID, PERSONA_C_PHONE, now, now),
    )
    return {
        "id": PERSONA_C_ID,
        "name": "Test Beneficiary C",
        "phone": PERSONA_C_PHONE,
        "district": "Moradabad",
        "block": "Chhajlet",
        "persona_type": "accessibility_preference",
    }


def seed_persona_e_with_referral(conn) -> Dict[str, Any]:
    """
    Persona E: Beneficiary with Active Referral / Case
    - Pre-seeded active referral in beneficiary_cases table
    - Expected: Can view only own referral status via IVR
    """
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT OR REPLACE INTO beneficiaries (
            id, name, phone, district, block, created_at, updated_at
        ) VALUES (?, 'Test Beneficiary E', ?, 'Moradabad', 'Kundarki', ?, ?);
        """,
        (PERSONA_E_ID, PERSONA_E_PHONE, now, now),
    )

    case_id = f"case_{PERSONA_E_ID}"
    conn.execute(
        """
        INSERT OR REPLACE INTO beneficiary_cases (
            id, beneficiary_id, district_id, block_id, case_status, created_at, updated_at
        ) VALUES (?, ?, 'Moradabad', 'Kundarki', 'under_review', ?, ?);
        """,
        (case_id, PERSONA_E_ID, now, now),
    )
    return {
        "id": PERSONA_E_ID,
        "name": "Test Beneficiary E",
        "phone": PERSONA_E_PHONE,
        "case_id": case_id,
        "case_status": "under_review",
    }


def seed_verified_training_and_schemes(conn, count: int = 5):
    """
    Seeds published training courses and verified qualifications into the database.
    Used to test 3-result limits and verified catalogue assertions.
    """
    now = datetime.now(timezone.utc).isoformat()
    for i in range(1, count + 1):
        # Training course
        cid = f"test_course_{i:02d}"
        conn.execute(
            """
            INSERT OR REPLACE INTO training_courses (
                id, title, slug, short_description, long_description, sector,
                nsqf_level, duration_hours, difficulty, language_code, source_name,
                verification_status, verified_at, last_updated_at, is_published
            ) VALUES (?, ?, ?, ?, ?, 'Apparel', '3', 120, 'Beginner', 'hi', 'PM-AJAY Skills', 'Verified', ?, ?, 1);
            """,
            (
                cid,
                f"सिलाई एवं परिधान स्तर {i}",
                f"tailoring-level-{i}",
                f"सिलाई एवं परिधान कोर्स {i}",
                f"सिलाई एवं परिधान विस्तृत विवरण {i}",
                now,
                now,
            ),
        )

        # Qualification / scheme
        qid = f"test_qual_{i:02d}"
        conn.execute(
            """
            INSERT OR REPLACE INTO qualifications (
                id, title, description, sector, nsqf_level, verification_status, created_at, updated_at
            ) VALUES (?, ?, ?, 'Apparel', 3, 'VERIFIED', ?, ?);
            """,
            (qid, f"पीएम-अजय कौशल प्रमाणन {i}", f"विवरण {i}", now, now),
        )
