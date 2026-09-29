import pandas as pd
from ml_model.src.ranking.eligibility import filter_eligible_courses
from ml_model.src.feature_engineering.features import compute_pair_features

def content_based_recommend(beneficiary: dict, courses_df: pd.DataFrame, top_k: int = 5) -> list:
    """
    Content-based fallback recommendation when no trained ML model is available.
    
    Uses weighted scoring from profile-course feature matches:
    - Career interest match: weight 0.20
    - Skill compatibility: weight 0.20
    - Education eligibility: weight 0.15
    - Local demand: weight 0.12
    - Language match: weight 0.10
    - Distance penalty: weight 0.08
    - Training mode match: weight 0.08
    - Age eligibility: weight 0.07
    
    Returns same format as rank_courses().
    """
    weights = {
        'career_interest_match': 0.20,
        'skill_match_score': 0.20,
        'education_eligibility': 0.15,
        'local_demand_score': 0.12,
        'language_match': 0.10,
        'distance_penalty': 0.08,
        'training_mode_match': 0.08,
        'age_eligibility': 0.07
    }
    
    # 1. Apply eligibility filter
    eligible_courses = filter_eligible_courses(beneficiary, courses_df)
    
    if eligible_courses.empty:
        return []
        
    results = []
    
    # 2. Compute weighted scores
    for _, course_row in eligible_courses.iterrows():
        try:
            features = compute_pair_features(beneficiary, course_row.to_dict())
            
            score = 0.0
            for feat, weight in weights.items():
                score += float(features.get(feat, 0)) * weight
                
            # Generate rule-based explanations
            explanations = []
            if features.get('career_interest_match', 0) == 1:
                explanations.append(f"[+] Matches {course_row.get('sector', 'chosen')} career interest")
            if features.get('education_eligibility', 0) == 1:
                explanations.append(f"[+] Meets education requirement ({beneficiary.get('education_level', '')})")
            if features.get('skill_match_score', 0) > 0.6:
                explanations.append(f"[+] High skill compatibility (score: {features.get('skill_match_score'):.2f})")
            if features.get('language_match', 0) == 1:
                explanations.append(f"[+] Preferred language ({course_row.get('language', '')}) available")
            if features.get('distance_penalty', 0) > 0.7:
                dist = features.get('distance_to_training_center_km', 0)
                explanations.append(f"[+] Training center is nearby ({dist:.0f} km)")
            if features.get('age_eligibility', 0) == 1:
                explanations.append("[+] Age within eligible range")
            if features.get('training_mode_match', 0) == 1:
                explanations.append(f"[+] Preferred training mode ({course_row.get('delivery_mode', '')}) available")
            if features.get('local_demand_score', 0) > 0.5:
                explanations.append("[+] High local job demand")
            if features.get('nsqf_appropriateness', 0) > 0.7:
                explanations.append("[+] Appropriate NSQF level for education")

            results.append({
                'course_id': course_row.get('course_id'),
                'course_name': course_row.get('course_name'),
                'sector': course_row.get('sector'),
                'nsqf_level': course_row.get('nsqf_level'),
                'score': score,
                'explanations': explanations
            })
        except Exception as e:
            continue
            
    # 3. Sort and limit
    results.sort(key=lambda x: x['score'], reverse=True)
    top_results = results[:top_k]
    for idx, res in enumerate(top_results):
        res['rank'] = idx + 1
        
    return top_results
