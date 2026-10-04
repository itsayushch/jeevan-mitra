import pytest
from app.services.recommendation_explanation_service import (
    RecommendationExplanationService,
    ExplanationFactor,
    FORBIDDEN_LLM_CLAIMS
)
from app.schemas.locale import SupportedLocale

def test_explanation_facts_confirmed_interests():
    profile = {
        "interests": ["Retail Sales", "Customer Service"],
        "education": "12th Pass",
        "district": "Pune",
        "mobility": 15,
        "work_preference": "wage_employment"
    }
    qualification = {
        "title": "Retail Sales Associate",
        "sector": "Retail"
    }
    
    facts = RecommendationExplanationService.build_explanation_facts(
        profile=profile,
        qualification=qualification,
        matched_skills=["Communication", "Cash Handling"],
        skill_gaps=["Inventory Management"],
        match_state="INTEREST_MATCH"
    )
    
    factor_names = [f["factor"] for f in facts]
    assert ExplanationFactor.INTEREST_MATCH.value in factor_names
    assert ExplanationFactor.EXISTING_SKILL_MATCH.value in factor_names
    assert ExplanationFactor.EDUCATION_COMPATIBILITY.value in factor_names
    assert ExplanationFactor.LOCATION_RELEVANCE.value in factor_names
    assert ExplanationFactor.TRAVEL_FEASIBILITY.value in factor_names
    assert ExplanationFactor.WORK_PREFERENCE_MATCH.value in factor_names
    assert ExplanationFactor.SKILL_GAP_RELEVANCE.value in factor_names
    # Strict invariant: VERIFIED_LOCAL_AVAILABILITY must NEVER appear for INTEREST_MATCH
    assert ExplanationFactor.VERIFIED_LOCAL_AVAILABILITY.value not in factor_names

def test_explanation_facts_no_unconfirmed_claims():
    # Empty profile: no interests, no skills, no mobility
    profile = {}
    qualification = {
        "title": "General Duty Assistant",
        "sector": "Healthcare"
    }
    facts = RecommendationExplanationService.build_explanation_facts(
        profile=profile,
        qualification=qualification,
        matched_skills=[],
        skill_gaps=[],
        match_state="INTEREST_MATCH"
    )
    # Should not fabricate interest or skills
    factor_names = [f["factor"] for f in facts]
    assert ExplanationFactor.INTEREST_MATCH.value not in factor_names
    assert ExplanationFactor.EXISTING_SKILL_MATCH.value not in factor_names
    assert ExplanationFactor.LOCATION_RELEVANCE.value not in factor_names
    assert ExplanationFactor.VERIFIED_LOCAL_AVAILABILITY.value not in factor_names

def test_verified_local_availability_only_for_verified_match():
    profile = {"district": "Nashik"}
    qualification = {"title": "Solar Technician", "sector": "Green Energy"}
    opp = {"centre_or_employer_name": "Nashik Pradhan Mantri Kaushal Kendra", "status": "active"}

    # Case 1: Match state is INTEREST_MATCH -> even with opp, availability factor must NOT be included
    facts_interest = RecommendationExplanationService.build_explanation_facts(
        profile=profile,
        qualification=qualification,
        match_state="INTEREST_MATCH",
        best_opp=opp
    )
    assert ExplanationFactor.VERIFIED_LOCAL_AVAILABILITY.value not in [f["factor"] for f in facts_interest]

    # Case 2: Match state is VERIFIED_MATCH -> availability factor MUST be included
    facts_verified = RecommendationExplanationService.build_explanation_facts(
        profile=profile,
        qualification=qualification,
        match_state="VERIFIED_MATCH",
        best_opp=opp
    )
    assert ExplanationFactor.VERIFIED_LOCAL_AVAILABILITY.value in [f["factor"] for f in facts_verified]
    avail_fact = next(f for f in facts_verified if f["factor"] == ExplanationFactor.VERIFIED_LOCAL_AVAILABILITY.value)
    assert "Nashik Pradhan Mantri Kaushal Kendra" in avail_fact["value"]

def test_template_explanation_english_and_hindi():
    facts = [
        {
            "factor": ExplanationFactor.INTEREST_MATCH.value,
            "value": "Sewing",
            "source": "profile.interests",
            "confidence": "CONFIRMED"
        },
        {
            "factor": ExplanationFactor.LOCATION_RELEVANCE.value,
            "value": "Thane",
            "source": "profile.district",
            "confidence": "CONFIRMED"
        }
    ]

    en_res = RecommendationExplanationService.render_template_explanation(
        locale=SupportedLocale.EN,
        facts=facts,
        title="Self Employed Tailor"
    )
    assert "Matches your confirmed interest in Sewing." in [r["text"] for r in en_res["reasons"]]
    assert "Available within your district (Thane)." in [r["text"] for r in en_res["reasons"]]
    assert en_res["locale"] == "en"

    hi_res = RecommendationExplanationService.render_template_explanation(
        locale=SupportedLocale.HI,
        facts=facts,
        title="Self Employed Tailor"
    )
    assert "Sewing में आपकी पुष्टि की गई रुचि से मेल खाता है।" in [r["text"] for r in hi_res["reasons"]]
    assert "आपके जिले (Thane) में उपलब्ध है।" in [r["text"] for r in hi_res["reasons"]]
    assert hi_res["locale"] == "hi"

def test_validate_llm_explanation_safety_guardrails():
    # Compliant text passes
    valid_text = "This course matches your interest in healthcare and is within your district."
    assert RecommendationExplanationService.validate_llm_explanation(valid_text) is True

    # Hallucinated guarantee or false assurance is strictly rejected
    for claim in FORBIDDEN_LLM_CLAIMS:
        bad_text = f"This course provides a 100% {claim} for every candidate."
        assert RecommendationExplanationService.validate_llm_explanation(bad_text) is False

def test_recommendation_invariants_preserved():
    # Verifies that explanation generation preserves ranking, scores, and matchState
    from app.services.recommendation_service import RecommendationService
    
    mock_item = {
        "recommendation_id": "rec-123",
        "rank": 1,
        "score": 0.95,
        "match_state": "VERIFIED_MATCH",
        "title": "Solar Panel Technician",
        "sector": "Green Energy",
        "qualification": {"title": "Solar Panel Technician", "sector": "Green Energy"},
        "matched_skills": ["Electrical wiring"],
        "skill_gaps": ["Solar inverter installation"],
        "local_availability": {
            "has_open_batch": True,
            "district": "Pune",
            "centre_name": "PMKK Pune"
        }
    }

    profile = {"interests": ["Solar"], "district": "Pune"}

    explanation = RecommendationExplanationService.build_recommendation_explanation(
        profile=profile,
        rec_item=mock_item,
        locale=SupportedLocale.EN
    )

    assert "shortExplanation" in explanation
    assert len(explanation["reasons"]) >= 1
    # Check that score, rank, and match_state are completely unaltered
    assert mock_item["rank"] == 1
    assert mock_item["score"] == 0.95
    assert mock_item["match_state"] == "VERIFIED_MATCH"
