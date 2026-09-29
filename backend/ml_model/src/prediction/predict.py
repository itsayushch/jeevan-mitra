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
        "beneficiary_id": "TEST_01_IT",
        "age": 21,
        "gender": "Male",
        "state": "West Bengal",
        "district": "Durgapur",
        "rural_urban": "Urban",
        "education_level": "Graduate",
        "education_stream": "Computer Science",
        "annual_family_income": 180000,
        "employment_status": "Unemployed",
        "current_occupation": "None",
        "work_experience_years": 0,
        "digital_literacy": 8,
        "communication_skill": 7,
        "numerical_skill": 7,
        "technical_skill": 8,
        "entrepreneurial_skill": 5,
        "existing_skill_level": "Intermediate",
        "career_interest": "Information Technology",
        "preferred_occupation": "Data Entry Operator",
        "preferred_industry": "Information Technology",
        "preferred_work_type": "Full_Time",
        "preferred_training_mode": "Offline",
        "preferred_language": "Hindi",
        "distance_to_training_center_km": 5,
        "training_center_availability": "Yes",
        "local_job_demand": "High",
        "local_industry": "Information Technology",
        "previous_training": "No",
        "previous_training_count": 0,
        "training_completion_rate": 0.0,
        "preferred_duration": "Medium",
    },

    {
        "beneficiary_id": "TEST_02_HEALTHCARE",
        "age": 24,
        "gender": "Female",
        "state": "West Bengal",
        "district": "Durgapur",
        "rural_urban": "Urban",
        "education_level": "Graduate",
        "education_stream": "Science",
        "annual_family_income": 200000,
        "employment_status": "Unemployed",
        "current_occupation": "None",
        "work_experience_years": 0,
        "digital_literacy": 6,
        "communication_skill": 8,
        "numerical_skill": 6,
        "technical_skill": 5,
        "entrepreneurial_skill": 4,
        "existing_skill_level": "Beginner",
        "career_interest": "Healthcare",
        "preferred_occupation": "Healthcare Assistant",
        "preferred_industry": "Healthcare",
        "preferred_work_type": "Full_Time",
        "preferred_training_mode": "Offline",
        "preferred_language": "Hindi",
        "distance_to_training_center_km": 7,
        "training_center_availability": "Yes",
        "local_job_demand": "High",
        "local_industry": "Healthcare",
        "previous_training": "No",
        "previous_training_count": 0,
        "training_completion_rate": 0.0,
        "preferred_duration": "Medium",
    },

    {
        "beneficiary_id": "TEST_03_AGRICULTURE",
        "age": 32,
        "gender": "Male",
        "state": "West Bengal",
        "district": "Durgapur",
        "rural_urban": "Rural",
        "education_level": "Class 10",
        "education_stream": "Not_Applicable",
        "annual_family_income": 120000,
        "employment_status": "Self_Employed",
        "current_occupation": "Farmer",
        "work_experience_years": 8,
        "digital_literacy": 4,
        "communication_skill": 5,
        "numerical_skill": 6,
        "technical_skill": 6,
        "entrepreneurial_skill": 7,
        "existing_skill_level": "Intermediate",
        "career_interest": "Agriculture",
        "preferred_occupation": "Agriculture Worker",
        "preferred_industry": "Agriculture",
        "preferred_work_type": "Self_Employment",
        "preferred_training_mode": "Offline",
        "preferred_language": "Bengali",
        "distance_to_training_center_km": 8,
        "training_center_availability": "Yes",
        "local_job_demand": "High",
        "local_industry": "Agriculture",
        "previous_training": "Yes",
        "previous_training_count": 1,
        "training_completion_rate": 0.8,
        "preferred_duration": "Short",
    },

    {
        "beneficiary_id": "TEST_04_CONSTRUCTION",
        "age": 29,
        "gender": "Male",
        "state": "West Bengal",
        "district": "Durgapur",
        "rural_urban": "Urban",
        "education_level": "Class 10",
        "education_stream": "Not_Applicable",
        "annual_family_income": 150000,
        "employment_status": "Employed",
        "current_occupation": "Helper",
        "work_experience_years": 5,
        "digital_literacy": 3,
        "communication_skill": 5,
        "numerical_skill": 5,
        "technical_skill": 8,
        "entrepreneurial_skill": 5,
        "existing_skill_level": "Intermediate",
        "career_interest": "Construction",
        "preferred_occupation": "Electrician",
        "preferred_industry": "Construction",
        "preferred_work_type": "Full_Time",
        "preferred_training_mode": "Offline",
        "preferred_language": "Bengali",
        "distance_to_training_center_km": 6,
        "training_center_availability": "Yes",
        "local_job_demand": "High",
        "local_industry": "Construction",
        "previous_training": "Yes",
        "previous_training_count": 2,
        "training_completion_rate": 0.9,
        "preferred_duration": "Medium",
    },

    {
        "beneficiary_id": "TEST_05_RETAIL",
        "age": 26,
        "gender": "Female",
        "state": "West Bengal",
        "district": "Durgapur",
        "rural_urban": "Urban",
        "education_level": "Class 12",
        "education_stream": "Commerce",
        "annual_family_income": 170000,
        "employment_status": "Unemployed",
        "current_occupation": "None",
        "work_experience_years": 1,
        "digital_literacy": 6,
        "communication_skill": 8,
        "numerical_skill": 7,
        "technical_skill": 4,
        "entrepreneurial_skill": 6,
        "existing_skill_level": "Beginner",
        "career_interest": "Retail",
        "preferred_occupation": "Retail Sales Associate",
        "preferred_industry": "Retail",
        "preferred_work_type": "Full_Time",
        "preferred_training_mode": "Offline",
        "preferred_language": "Hindi",
        "distance_to_training_center_km": 4,
        "training_center_availability": "Yes",
        "local_job_demand": "High",
        "local_industry": "Retail",
        "previous_training": "No",
        "previous_training_count": 0,
        "training_completion_rate": 0.0,
        "preferred_duration": "Short",
    },

    {
        "beneficiary_id": "TEST_06_ENTREPRENEUR",
        "age": 35,
        "gender": "Male",
        "state": "West Bengal",
        "district": "Durgapur",
        "rural_urban": "Urban",
        "education_level": "Graduate",
        "education_stream": "Commerce",
        "annual_family_income": 250000,
        "employment_status": "Self_Employed",
        "current_occupation": "Small Business Owner",
        "work_experience_years": 7,
        "digital_literacy": 7,
        "communication_skill": 8,
        "numerical_skill": 8,
        "technical_skill": 5,
        "entrepreneurial_skill": 9,
        "existing_skill_level": "Intermediate",
        "career_interest": "Entrepreneurship",
        "preferred_occupation": "Business Owner",
        "preferred_industry": "Entrepreneurship",
        "preferred_work_type": "Self_Employment",
        "preferred_training_mode": "Offline",
        "preferred_language": "Hindi",
        "distance_to_training_center_km": 10,
        "training_center_availability": "Yes",
        "local_job_demand": "Medium",
        "local_industry": "Entrepreneurship",
        "previous_training": "Yes",
        "previous_training_count": 1,
        "training_completion_rate": 0.9,
        "preferred_duration": "Medium",
    },

    {
        "beneficiary_id": "TEST_07_AUTOMOTIVE",
        "age": 27,
        "gender": "Male",
        "state": "West Bengal",
        "district": "Durgapur",
        "rural_urban": "Urban",
        "education_level": "Class 12",
        "education_stream": "Science",
        "annual_family_income": 160000,
        "employment_status": "Unemployed",
        "current_occupation": "None",
        "work_experience_years": 0,
        "digital_literacy": 5,
        "communication_skill": 5,
        "numerical_skill": 6,
        "technical_skill": 9,
        "entrepreneurial_skill": 5,
        "existing_skill_level": "Intermediate",
        "career_interest": "Automotive",
        "preferred_occupation": "Automotive Technician",
        "preferred_industry": "Automotive",
        "preferred_work_type": "Full_Time",
        "preferred_training_mode": "Offline",
        "preferred_language": "Bengali",
        "distance_to_training_center_km": 9,
        "training_center_availability": "Yes",
        "local_job_demand": "High",
        "local_industry": "Automotive",
        "previous_training": "No",
        "previous_training_count": 0,
        "training_completion_rate": 0.0,
        "preferred_duration": "Long",
    },

    {
        "beneficiary_id": "TEST_08_LOGISTICS",
        "age": 23,
        "gender": "Male",
        "state": "West Bengal",
        "district": "Durgapur",
        "rural_urban": "Urban",
        "education_level": "Class 12",
        "education_stream": "Commerce",
        "annual_family_income": 140000,
        "employment_status": "Unemployed",
        "current_occupation": "None",
        "work_experience_years": 0,
        "digital_literacy": 7,
        "communication_skill": 6,
        "numerical_skill": 7,
        "technical_skill": 5,
        "entrepreneurial_skill": 5,
        "existing_skill_level": "Beginner",
        "career_interest": "Logistics",
        "preferred_occupation": "Logistics Associate",
        "preferred_industry": "Logistics",
        "preferred_work_type": "Full_Time",
        "preferred_training_mode": "Offline",
        "preferred_language": "Hindi",
        "distance_to_training_center_km": 5,
        "training_center_availability": "Yes",
        "local_job_demand": "High",
        "local_industry": "Logistics",
        "previous_training": "No",
        "previous_training_count": 0,
        "training_completion_rate": 0.0,
        "preferred_duration": "Medium",
    },

    {
        "beneficiary_id": "TEST_09_BEAUTY",
        "age": 22,
        "gender": "Female",
        "state": "West Bengal",
        "district": "Durgapur",
        "rural_urban": "Urban",
        "education_level": "Class 10",
        "education_stream": "Not_Applicable",
        "annual_family_income": 110000,
        "employment_status": "Unemployed",
        "current_occupation": "None",
        "work_experience_years": 0,
        "digital_literacy": 4,
        "communication_skill": 7,
        "numerical_skill": 4,
        "technical_skill": 6,
        "entrepreneurial_skill": 7,
        "existing_skill_level": "Beginner",
        "career_interest": "Beauty & Wellness",
        "preferred_occupation": "Beauty Therapist",
        "preferred_industry": "Beauty & Wellness",
        "preferred_work_type": "Self_Employment",
        "preferred_training_mode": "Offline",
        "preferred_language": "Bengali",
        "distance_to_training_center_km": 6,
        "training_center_availability": "Yes",
        "local_job_demand": "Medium",
        "local_industry": "Beauty & Wellness",
        "previous_training": "No",
        "previous_training_count": 0,
        "training_completion_rate": 0.0,
        "preferred_duration": "Short",
    },

    {
        "beneficiary_id": "TEST_10_BANKING",
        "age": 30,
        "gender": "Female",
        "state": "West Bengal",
        "district": "Durgapur",
        "rural_urban": "Urban",
        "education_level": "Graduate",
        "education_stream": "Commerce",
        "annual_family_income": 220000,
        "employment_status": "Unemployed",
        "current_occupation": "None",
        "work_experience_years": 1,
        "digital_literacy": 8,
        "communication_skill": 8,
        "numerical_skill": 9,
        "technical_skill": 6,
        "entrepreneurial_skill": 5,
        "existing_skill_level": "Intermediate",
        "career_interest": "Banking / Finance",
        "preferred_occupation": "Banking Associate",
        "preferred_industry": "Banking / Finance",
        "preferred_work_type": "Full_Time",
        "preferred_training_mode": "Offline",
        "preferred_language": "Hindi",
        "distance_to_training_center_km": 7,
        "training_center_availability": "Yes",
        "local_job_demand": "High",
        "local_industry": "Banking / Finance",
        "previous_training": "No",
        "previous_training_count": 0,
        "training_completion_rate": 0.0,
        "preferred_duration": "Medium",
    },

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
