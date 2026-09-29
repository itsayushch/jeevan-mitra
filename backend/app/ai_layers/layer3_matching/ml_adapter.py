"""Optional ML ordering of candidates that have already passed main's filters.

The model cannot add qualifications, claim available seats, or change match
states. Missing dependencies/artifacts preserve the deterministic score.
"""
import math
from typing import Any

from app.config import settings
from app.ai_layers.layer2_extraction.validation import education_to_rank
from app.utils.logger import logger

EDUCATION = ('No_Formal', 'Primary', 'Middle', 'Secondary',
             'Senior_Secondary', 'Graduate', 'Post_Graduate')


def _predict(profile: dict, courses: list[dict]) -> dict:
    # Keep the normal FastAPI installation independent of the ML dependency set.
    import pandas as pd
    from ml_model.src.prediction.predict import predict
    return predict(profile, top_k=len(courses), courses_df=pd.DataFrame(courses))


def rerank_candidates(candidates: list[dict[str, Any]], profile: dict,
                      qualifications: dict[str, dict]) -> None:
    if not settings.ML_RANKING_ENABLED or not candidates:
        return
    try:
        unknown = float('nan')
        model_profile = {
            'education_level': EDUCATION[education_to_rank(str(
                profile.get('education') or profile.get('education_level') or ''))],
            'career_interest': ', '.join(profile.get('interests', []))
                if isinstance(profile.get('interests'), list) else profile.get('interests', 'Unknown'),
            'district': profile.get('district', 'Unknown'),
            'state': profile.get('state', 'Unknown'),
            'current_occupation': profile.get('current_work', 'Unknown'),
            'preferred_language': {'hi': 'Hindi', 'en': 'English'}.get(
                profile.get('language'), 'Unknown'),
            'preferred_work_type': {'wage': 'Full_Time', 'self_employment': 'Self_Employment'}.get(
                profile.get('self_employment_or_wage_preference') or profile.get('work_preference'), 'Unknown'),
            'existing_skill_level': 'Unknown', 'preferred_training_mode': 'Unknown',
            'preferred_duration': 'Unknown', 'training_center_availability': 'Unknown',
            'local_job_demand': 'Unknown', 'previous_training': 'Unknown',
            'employment_status': 'Unknown',
        }
        for field in ('age', 'annual_family_income', 'work_experience_years',
                      'digital_literacy', 'communication_skill', 'numerical_skill',
                      'technical_skill', 'entrepreneurial_skill', 'previous_training_count',
                      'training_completion_rate', 'distance_to_training_center_km'):
            model_profile[field] = profile.get(field, unknown)

        courses = []
        for candidate in candidates:
            qid = candidate['qualification']['internal_id']
            qual = qualifications[qid]
            opportunity = candidate.get('best_opp') or {}
            courses.append({
                'course_id': qid, 'course_name': qual['title'], 'sector': qual['sector'],
                'nsqf_level': qual['nsqf_level'], 'course_duration_hours': qual['duration_hours'],
                'minimum_education': EDUCATION[education_to_rank(qual.get('min_education', ''))],
                'required_skill_level': 'Unknown', 'age_min': unknown, 'age_max': unknown,
                'delivery_mode': 'Unknown', 'language': '', 'average_salary': unknown,
                'local_demand': 'Unknown', 'industry': qual['sector'],
                'distance_to_training_center_km': opportunity.get('distance_km', unknown),
            })
        result = _predict(model_profile, courses)
        if result.get('method') != 'ml_model':
            logger.warning('ML ranking unavailable; retaining deterministic ranking')
            return
        scores = {r['course_id']: float(r['score']) for r in result['recommendations']}
        expected = {c['qualification']['internal_id'] for c in candidates}
        if set(scores) != expected or any(not math.isfinite(s) or not 0 <= s <= 1 for s in scores.values()):
            raise ValueError('ML output must score exactly the eligible catalogue candidates')
        for candidate in candidates:
            base = candidate['score']
            ml_score = scores[candidate['qualification']['internal_id']]
            candidate['ranking_factors'].update({
                'deterministic_score': base, 'ml_score': ml_score,
                'ml_weight': 0.2, 'ml_training_data': 'synthetic',
            })
            candidate['score'] = round(0.8 * base + 20 * ml_score, 1)
    except Exception as exc:
        logger.warning('ML ranking unavailable (%s); retaining deterministic ranking', type(exc).__name__)
