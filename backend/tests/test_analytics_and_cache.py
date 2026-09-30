import pytest
import uuid
import json
from datetime import datetime, timezone
from app.database import get_db
from app.services.analytics_service import AnalyticsService, ALLOWED_ANALYTICS_EVENTS
from app.services.recommendation_explanation_service import RecommendationExplanationService
from app.schemas.locale import SupportedLocale

def test_analytics_sanitization_and_privacy():
    with get_db() as conn:
        # 1. Test that sensitive text fields are stripped
        raw_meta = {
            "mode": "voice",
            "locale": "hi",
            "character_length": 45,
            "raw_text": "Sensitive user text about medical diagnosis",
            "transcript": "Secret audio transcript that should never be in analytics",
            "phone": "+919876543210",
            "notes": "Private counselor notes"
        }

        sanitized = AnalyticsService.sanitize_metadata(raw_meta)
        assert "raw_text" not in sanitized
        assert "transcript" not in sanitized
        assert "phone" not in sanitized
        assert "notes" not in sanitized
        assert sanitized["mode"] == "voice"
        assert sanitized["character_length"] == 45

        # 2. Record allowed event
        evt_id = AnalyticsService.record_event(
            conn=conn,
            event_name="locale.selected",
            actor_type="beneficiary",
            district_id="Moradabad",
            locale="hi",
            metadata=raw_meta
        )
        assert evt_id is not None
        assert evt_id.startswith("evt_")

        # 3. Verify event stored in DB has only sanitized metadata
        row = conn.execute("SELECT * FROM analytics_events WHERE id = ?", (evt_id,)).fetchone()
        assert row is not None
        stored_meta = json.loads(row["metadata_json"])
        assert "raw_text" not in stored_meta
        assert "transcript" not in stored_meta
        assert stored_meta["mode"] == "voice"

def test_analytics_k_anonymity_suppression():
    with get_db() as conn:
        district = f"Dist_{uuid.uuid4().hex[:6]}"
        # Record 3 events for a specific locale (below threshold 5)
        for _ in range(3):
            AnalyticsService.record_event(
                conn=conn,
                event_name="opportunity_submission.submitted",
                district_id=district,
                locale="hi"
            )

        # Record 7 events for english (above threshold 5)
        for _ in range(7):
            AnalyticsService.record_event(
                conn=conn,
                event_name="opportunity_submission.submitted",
                district_id=district,
                locale="en"
            )

        summary = AnalyticsService.get_aggregated_metrics(conn, district_id=district, k_threshold=5)
        metrics = summary["metrics"]["opportunity_submission.submitted"]

        # Below 5 is suppressed to protect small groups
        assert metrics["hi"] == "<SUPPRESSED_BELOW_K>"
        # Above 5 is exposed
        assert metrics["en"] >= 7

def test_disposable_explanation_cache():
    rec_id = f"rec_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    facts = [
        {"factor": "INTEREST_MATCH", "value": "Solar energy", "source": "profile.interests", "confidence": "CONFIRMED"}
    ]

    with get_db() as conn:
        # Create dummy recommendation
        conn.execute("""
            INSERT INTO recommendations (
                id, beneficiary_id, qualification_id, rank, score, score_breakdown, match_state,
                explanation_text, audio_explanation_script, tradeoff_summary, skill_gap_summary,
                data_snapshot, matched_skills, skill_gaps, explanation_facts, created_at, updated_at
            ) VALUES (?, 'ben_test', 'qual_test', 1, 0.9, '{}', 'INTEREST_MATCH', 'expl', 'script', 'tradeoff', 'gap', '{}', '[]', '[]', ?, ?, ?);
        """, (rec_id, json.dumps(facts), now, now))

        # First call renders and caches
        expl1 = RecommendationExplanationService.get_explanation(
            locale=SupportedLocale.EN,
            facts=facts,
            title="Solar Technician",
            match_state="INTEREST_MATCH",
            conn=conn,
            recommendation_id=rec_id
        )
        assert "shortExplanation" in expl1

        # Check cache table has the record
        cache_row = conn.execute("SELECT * FROM recommendation_explanation_cache WHERE recommendation_id = ? AND locale = 'en';", (rec_id,)).fetchone()
        assert cache_row is not None
        assert cache_row["renderer"] == "template"

        # Second call returns from cache
        expl2 = RecommendationExplanationService.get_explanation(
            locale=SupportedLocale.EN,
            facts=facts,
            title="Solar Technician",
            match_state="INTEREST_MATCH",
            conn=conn,
            recommendation_id=rec_id
        )
        assert expl2["shortExplanation"] == expl1["shortExplanation"]
