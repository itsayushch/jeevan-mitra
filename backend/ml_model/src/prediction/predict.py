import os
import json
import numpy as np
import pandas as pd
from src.ranking.ranker import rank_courses
from src.ranking.fallback import content_based_recommend

def predict(beneficiary_profile: dict, top_k: int = 5, use_fallback: bool = False) -> dict:
    """
    Main inference function.
    
    Input: beneficiary profile dict with keys matching the beneficiary columns.
    Not all keys are required - missing values will be handled by the preprocessor.
    
    Output: dict with recommendations
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_path = os.path.join(project_root, 'models', 'best_model.pkl')
    courses_path = os.path.join(project_root, 'data', 'reference', 'courses.csv')
    
    try:
        courses_df = pd.read_csv(courses_path)
    except FileNotFoundError:
        courses_df = pd.DataFrame()
        
    ben_id = beneficiary_profile.get('beneficiary_id', 'UNKNOWN_BEN')
    
    # Fill missing beneficiary profile keys so preprocessor receives complete feature set
    full_profile = {
        'age': np.nan, 'gender': 'Unknown', 'state': 'Unknown', 'district': 'Unknown',
        'rural_urban': 'Unknown', 'social_category': 'Unknown', 'education_level': 'Middle',
        'education_stream': 'Not_Applicable', 'annual_family_income': np.nan,
        'employment_status': 'Unemployed', 'current_occupation': 'None',
        'work_experience_years': 0, 'digital_literacy': 5, 'communication_skill': 5,
        'numerical_skill': 5, 'technical_skill': 5, 'entrepreneurial_skill': 5,
        'existing_skill_level': 'Beginner', 'career_interest': 'Unknown',
        'preferred_occupation': 'Unknown', 'preferred_industry': 'Unknown',
        'preferred_work_type': 'Full_Time', 'preferred_training_mode': 'Offline',
        'preferred_language': 'Hindi', 'latitude': np.nan, 'longitude': np.nan,
        'distance_to_training_center_km': 10.0, 'training_center_availability': 'Yes',
        'local_job_demand': 'Medium', 'local_industry': 'Unknown',
        'previous_training': 'No', 'previous_training_count': 0,
        'training_completion_rate': 0.0, 'preferred_duration': 'Medium'
    }
    full_profile.update(beneficiary_profile)
    
    if use_fallback or not os.path.exists(model_path):
        method = 'content_based_fallback'
        recs = content_based_recommend(full_profile, courses_df, top_k)
    else:
        method = 'ml_model'
        try:
            recs = rank_courses(full_profile, courses_df, model_path, top_k)
        except Exception as e:
            print(f"ML model failed, falling back to content-based: {e}")
            method = 'content_based_fallback_due_to_error'
            recs = content_based_recommend(full_profile, courses_df, top_k)
            
    return {
        'beneficiary_id': ben_id,
        'method': method,
        'top_k': top_k,
        'recommendations': recs
    }

def run_sample_predictions():
    """Run predictions for several sample beneficiaries and print results."""
    samples = [
    {
        'beneficiary_id': 'TEST_IT',
        'age': 24,
        'state': 'Maharashtra',
        'rural_urban': 'Urban',
        'education_level': 'Graduate',
        'existing_skill_level': 'Intermediate',
        'career_interest': 'IT / ITES',
        'preferred_occupation': 'Web Developer',
        'preferred_industry': 'IT / ITES',
        'preferred_language': 'English',
        'digital_literacy': 9,
        'technical_skill': 8,
        'communication_skill': 7,
        'numerical_skill': 7
    },

    {
        'beneficiary_id': 'TEST_HEALTHCARE',
        'age': 25,
        'state': 'Tamil Nadu',
        'rural_urban': 'Urban',
        'education_level': 'Graduate',
        'existing_skill_level': 'Intermediate',
        'career_interest': 'Healthcare',
        'preferred_occupation': 'Healthcare Assistant',
        'preferred_industry': 'Healthcare',
        'preferred_language': 'Tamil',
        'digital_literacy': 6,
        'technical_skill': 6,
        'communication_skill': 8,
        'numerical_skill': 6
    },

    {
        'beneficiary_id': 'TEST_AGRICULTURE',
        'age': 30,
        'state': 'Uttar Pradesh',
        'rural_urban': 'Rural',
        'education_level': 'Higher_Secondary',
        'existing_skill_level': 'Beginner',
        'career_interest': 'Agriculture',
        'preferred_occupation': 'Organic Farming Technician',
        'preferred_industry': 'Agriculture',
        'preferred_language': 'Hindi',
        'digital_literacy': 4,
        'technical_skill': 5,
        'communication_skill': 5,
        'numerical_skill': 5
    },

    {
        'beneficiary_id': 'TEST_CONSTRUCTION',
        'age': 28,
        'state': 'Bihar',
        'rural_urban': 'Rural',
        'education_level': 'Higher_Secondary',
        'existing_skill_level': 'Beginner',
        'career_interest': 'Construction',
        'preferred_occupation': 'Electrician',
        'preferred_industry': 'Construction',
        'preferred_language': 'Hindi',
        'digital_literacy': 4,
        'technical_skill': 8,
        'communication_skill': 5,
        'numerical_skill': 6
    },

    {
        'beneficiary_id': 'TEST_AUTOMOTIVE',
        'age': 27,
        'state': 'West Bengal',
        'rural_urban': 'Urban',
        'education_level': 'Higher_Secondary',
        'existing_skill_level': 'Intermediate',
        'career_interest': 'Automotive',
        'preferred_occupation': 'Automotive Specialist',
        'preferred_industry': 'Automotive',
        'preferred_language': 'Hindi',
        'digital_literacy': 5,
        'technical_skill': 9,
        'communication_skill': 5,
        'numerical_skill': 7
    },

    {
        'beneficiary_id': 'TEST_ELECTRONICS',
        'age': 23,
        'state': 'West Bengal',
        'rural_urban': 'Urban',
        'education_level': 'Diploma',
        'existing_skill_level': 'Intermediate',
        'career_interest': 'Electronics',
        'preferred_occupation': 'Electronics Specialist',
        'preferred_industry': 'Electronics',
        'preferred_language': 'English',
        'digital_literacy': 7,
        'technical_skill': 9,
        'communication_skill': 6,
        'numerical_skill': 8
    },

    {
        'beneficiary_id': 'TEST_RETAIL',
        'age': 22,
        'state': 'Maharashtra',
        'rural_urban': 'Urban',
        'education_level': 'Higher_Secondary',
        'existing_skill_level': 'Beginner',
        'career_interest': 'Retail',
        'preferred_occupation': 'Retail Specialist',
        'preferred_industry': 'Retail',
        'preferred_language': 'Hindi',
        'digital_literacy': 6,
        'technical_skill': 5,
        'communication_skill': 8,
        'numerical_skill': 6
    },

    {
        'beneficiary_id': 'TEST_TOURISM',
        'age': 24,
        'state': 'West Bengal',
        'rural_urban': 'Urban',
        'education_level': 'Graduate',
        'existing_skill_level': 'Intermediate',
        'career_interest': 'Tourism',
        'preferred_occupation': 'Tourism Specialist',
        'preferred_industry': 'Tourism',
        'preferred_language': 'English',
        'digital_literacy': 6,
        'technical_skill': 5,
        'communication_skill': 9,
        'numerical_skill': 5
    },

    {
        'beneficiary_id': 'TEST_HOSPITALITY',
        'age': 23,
        'state': 'Goa',
        'rural_urban': 'Urban',
        'education_level': 'Higher_Secondary',
        'existing_skill_level': 'Beginner',
        'career_interest': 'Hospitality',
        'preferred_occupation': 'Hospitality Specialist',
        'preferred_industry': 'Hospitality',
        'preferred_language': 'Hindi',
        'digital_literacy': 5,
        'technical_skill': 5,
        'communication_skill': 9,
        'numerical_skill': 5
    },

    {
        'beneficiary_id': 'TEST_BANKING',
        'age': 25,
        'state': 'West Bengal',
        'rural_urban': 'Urban',
        'education_level': 'Graduate',
        'existing_skill_level': 'Intermediate',
        'career_interest': 'Banking / Finance',
        'preferred_occupation': 'Banking / Finance Specialist',
        'preferred_industry': 'Banking / Finance',
        'preferred_language': 'English',
        'digital_literacy': 8,
        'technical_skill': 6,
        'communication_skill': 8,
        'numerical_skill': 9
    },

    {
        'beneficiary_id': 'TEST_BEAUTY',
        'age': 24,
        'state': 'West Bengal',
        'rural_urban': 'Urban',
        'education_level': 'Higher_Secondary',
        'existing_skill_level': 'Beginner',
        'career_interest': 'Beauty & Wellness',
        'preferred_occupation': 'Beauty & Wellness Specialist',
        'preferred_industry': 'Beauty & Wellness',
        'preferred_language': 'Hindi',
        'digital_literacy': 4,
        'technical_skill': 5,
        'communication_skill': 7,
        'numerical_skill': 4
    },

    {
        'beneficiary_id': 'TEST_LOGISTICS',
        'age': 26,
        'state': 'Maharashtra',
        'rural_urban': 'Urban',
        'education_level': 'Higher_Secondary',
        'existing_skill_level': 'Intermediate',
        'career_interest': 'Logistics',
        'preferred_occupation': 'Logistics Specialist',
        'preferred_industry': 'Logistics',
        'preferred_language': 'Hindi',
        'digital_literacy': 6,
        'technical_skill': 6,
        'communication_skill': 6,
        'numerical_skill': 7
    },

    {
        'beneficiary_id': 'TEST_MANUFACTURING',
        'age': 27,
        'state': 'Maharashtra',
        'rural_urban': 'Urban',
        'education_level': 'Diploma',
        'existing_skill_level': 'Intermediate',
        'career_interest': 'Manufacturing',
        'preferred_occupation': 'Manufacturing Specialist',
        'preferred_industry': 'Manufacturing',
        'preferred_language': 'Hindi',
        'digital_literacy': 5,
        'technical_skill': 9,
        'communication_skill': 5,
        'numerical_skill': 7
    },

    {
        'beneficiary_id': 'TEST_GREEN',
        'age': 25,
        'state': 'West Bengal',
        'rural_urban': 'Urban',
        'education_level': 'Graduate',
        'existing_skill_level': 'Intermediate',
        'career_interest': 'Green Jobs',
        'preferred_occupation': 'Green Jobs Specialist',
        'preferred_industry': 'Green Jobs',
        'preferred_language': 'Hindi',
        'digital_literacy': 6,
        'technical_skill': 7,
        'communication_skill': 6,
        'numerical_skill': 6
    },

    {
        'beneficiary_id': 'TEST_TELECOM',
        'age': 24,
        'state': 'West Bengal',
        'rural_urban': 'Urban',
        'education_level': 'Diploma',
        'existing_skill_level': 'Intermediate',
        'career_interest': 'Telecom',
        'preferred_occupation': 'Telecom Specialist',
        'preferred_industry': 'Telecom',
        'preferred_language': 'English',
        'digital_literacy': 8,
        'technical_skill': 9,
        'communication_skill': 6,
        'numerical_skill': 7
    },

    {
        'beneficiary_id': 'TEST_ENTREPRENEURSHIP',
        'age': 29,
        'state': 'West Bengal',
        'rural_urban': 'Urban',
        'education_level': 'Graduate',
        'existing_skill_level': 'Intermediate',
        'career_interest': 'Entrepreneurship',
        'preferred_occupation': 'Entrepreneurship Specialist',
        'preferred_industry': 'Entrepreneurship',
        'preferred_language': 'Hindi',
        'digital_literacy': 7,
        'technical_skill': 6,
        'communication_skill': 8,
        'numerical_skill': 8,
        'entrepreneurial_skill': 10
    }
]
    
    print("=" * 60)
    print("RUNNING SAMPLE PREDICTIONS")
    print("=" * 60)
    
    for sample in samples:
        print(f"\nProcessing {sample['beneficiary_id']} - {sample.get('career_interest')} interest...")
        res = predict(sample, top_k=3, use_fallback=False)
        
        print(f"Method used: {res['method']}")
        if not res['recommendations']:
            print("No recommendations found.")
        
        for rec in res['recommendations']:
            print(f"  [{rec['rank']}] {rec.get('course_id', '')} - {rec.get('course_name', '')} (Score: {rec['score']:.2f})")
            for exp in rec.get('explanations', []):
                print(f"      {exp}")

def run_sample_predictions_fallback():
    """Run fallback predictions for sample beneficiaries."""
    samples = [
        {'beneficiary_id': 'BEN_FALLBACK_1', 'age': 22, 'education_level': 'Secondary', 'career_interest': 'IT / ITES'}
    ]
    for sample in samples:
        res = predict(sample, top_k=3, use_fallback=True)
        print(json.dumps(res, indent=2))

if __name__ == '__main__':
    run_sample_predictions()
