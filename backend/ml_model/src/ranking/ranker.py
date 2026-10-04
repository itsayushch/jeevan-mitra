import os
import pandas as pd
import numpy as np
import joblib
from joblib.numpy_pickle import NumpyUnpickler
from ml_model.src.feature_engineering.encoders import FrequencyEncoder
from functools import lru_cache
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

from ml_model.src.ranking.eligibility import filter_eligible_courses
from ml_model.src.feature_engineering.features import compute_pair_features

@lru_cache(maxsize=1)
def load_model(model_path: str):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    # The contributed artifact refers to its old standalone training module.
    # Remap only that transformer without importing plotting/training libraries
    # or registering a global 'src' package that collides with backend code.
    class PortableUnpickler(NumpyUnpickler):
        def find_class(self, module, name):
            if module in ('src.training.train', '__main__') and name == 'FrequencyEncoder':
                return FrequencyEncoder
            return super().find_class(module, name)

    with open(model_path, 'rb') as handle:
        return PortableUnpickler(model_path, handle, ensure_native_byte_order=True).load()

def get_shap_explanations(model, preprocessor, feature_df, top_n_features=5):
    """Get SHAP values for the top features driving the prediction."""
    if not HAS_SHAP:
        return {}
    
    try:
        # Assuming the model is a pipeline: preprocessor + classifier
        X_transformed = preprocessor.transform(feature_df)
        
        classifier = model.named_steps.get('classifier', model)
        
        explainer = None
        if hasattr(classifier, 'estimators_'): # RandomForest, etc.
            explainer = shap.TreeExplainer(classifier)
        else:
            explainer = shap.Explainer(classifier, X_transformed)
            
        shap_values = explainer.shap_values(X_transformed)
        
        # If binary classification, take the positive class SHAP values
        if isinstance(shap_values, list) and len(shap_values) > 1:
            shap_values = shap_values[1]
            
        # Try to get feature names
        feature_names = feature_df.columns
        if hasattr(preprocessor, 'get_feature_names_out'):
            try:
                feature_names = preprocessor.get_feature_names_out()
            except:
                pass
                
        explanations = {}
        for i in range(len(feature_df)):
            instance_shap = shap_values[i]
            # Get top indices
            top_indices = np.argsort(np.abs(instance_shap))[-top_n_features:]
            
            exp_list = []
            for idx in reversed(top_indices):
                fname = feature_names[idx] if idx < len(feature_names) else f"Feature {idx}"
                fval = instance_shap[idx]
                if fval > 0: # Only positive contributors for recommendations
                    exp_list.append(f"↑ {fname} (+{fval:.2f})")
            
            explanations[i] = exp_list
            
        return explanations
    except Exception as e:
        print(f"SHAP explanation failed: {e}")
        return {}

def rank_courses(beneficiary: dict, courses_df: pd.DataFrame, model_path: str = None, top_k: int = 5) -> list:
    """
    Full recommendation pipeline:
    1. Filter eligible courses using eligibility.py
    2. For each eligible course, compute (beneficiary, course) pair features using features.py
    3. Score each pair using the trained ML model
    4. Sort by score descending
    5. Return top-K recommendations with explanations
    """
    if model_path is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = os.path.join(project_root, 'models', 'best_model.pkl')
        
    model = load_model(model_path)
    
    # Preprocessor might be separate or part of pipeline, assume pipeline handles it or load separately if needed.
    preprocessor = model.named_steps.get('preprocessor', None) if hasattr(model, 'named_steps') else model
    
    # 1. Filter eligible courses
    eligible_courses = filter_eligible_courses(beneficiary, courses_df)
    if eligible_courses.empty:
        return []
        
    # 2. Compute pair features
    feature_rows = []
    course_list = []
    
    for _, course_row in eligible_courses.iterrows():
        try:
            c_dict = course_row.to_dict()
            features = compute_pair_features(beneficiary, c_dict)
            
            row_data = {}
            row_data.update(beneficiary)
            row_data.update(c_dict)
            row_data.update(features)
            
            feature_rows.append(row_data)
            course_list.append(course_row)
        except Exception as e:
            continue
            
    if not feature_rows:
        return []
        
    feature_df = pd.DataFrame(feature_rows)
    
    # 3. Score each pair
    try:
        # Ensure correct column order if needed, assuming pipeline handles it
        scores = model.predict_proba(feature_df)[:, 1] # Probability of positive class
    except Exception as e:
        # Fallback if predict_proba is not available
        scores = model.predict(feature_df)
        
    # Optional SHAP explanations
    shap_exps = get_shap_explanations(model, preprocessor, feature_df)
        
    # 4. Sort and format results
    results = []
    for i, course_row in enumerate(course_list):
        features = feature_rows[i]
        raw_ml_score = float(scores[i])
        
        # Combine ML model probability with career match & skill match boost
        career_boost = 0.30 if features.get('career_interest_match', 0) == 1 else 0.0
        skill_boost = 0.20 * float(features.get('skill_match_score', 0))
        final_score = (0.50 * raw_ml_score) + career_boost + skill_boost
        score = float(final_score)
        
        # Rule-based explanations
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
            # lower distance is better, maybe penalty is inverted in this system
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
            
        # Append SHAP explanations if available
        if i in shap_exps:
            explanations.extend(shap_exps[i])
            
        results.append({
            'course_id': course_row.get('course_id'),
            'course_name': course_row.get('course_name'),
            'sector': course_row.get('sector'),
            'nsqf_level': course_row.get('nsqf_level'),
            'score': score,
            'explanations': explanations
        })
        
    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # 5. Return top-K
    top_results = results[:top_k]
    for idx, res in enumerate(top_results):
        res['rank'] = idx + 1
        
    return top_results
