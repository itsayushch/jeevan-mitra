import pandas as pd
import numpy as np

# Ordinal mappings
EDUCATION_ORDINAL = {
    'Unknown': -1,
    'No_Formal': 0,
    'Primary': 1,
    'Middle': 2,
    'Secondary': 3,
    'Senior_Secondary': 4,
    'Graduate': 5,
    'Post_Graduate': 6
}

SKILL_ORDINAL = {
    'Unknown': -1,
    'Beginner': 0,
    'Intermediate': 1,
    'Advanced': 2,
    'Expert': 3
}

def normalize_education(value):
    aliases = {
        'no formal education': 'No_Formal', 'class 5': 'Primary',
        'class 8': 'Middle', 'class 10': 'Secondary', 'class 12': 'Senior_Secondary',
        'iti / diploma': 'Senior_Secondary', 'post graduate': 'Post_Graduate',
    }
    value = str(value).strip()
    return aliases.get(value.lower(), next(
        (level for level in EDUCATION_ORDINAL if level.lower() == value.lower()), 'Unknown'))

def filter_eligible_courses(beneficiary: dict, courses_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply hard eligibility constraints to filter courses a beneficiary can actually join.
    
    Filters:
    1. Age: beneficiary age must be within [age_min, age_max]
    2. Education: beneficiary education_level must be >= course minimum_education
    3. Skill level: beneficiary existing_skill_level must be >= course required_skill_level
    
    Returns filtered DataFrame of eligible courses.
    """
    filtered_df = courses_df.copy()
    
    # 1. Age Filter
    ben_age = beneficiary.get('age', -1)
    if ben_age != -1 and not pd.isna(ben_age):
        filtered_df = filtered_df[
            (filtered_df['age_min'].isna() | (filtered_df['age_min'] <= ben_age)) & 
            (filtered_df['age_max'].isna() | (filtered_df['age_max'] >= ben_age))
        ]
        
    # 2. Education Filter
    ben_edu = normalize_education(beneficiary.get('education_level', 'Unknown'))
    ben_edu_val = EDUCATION_ORDINAL.get(ben_edu, -1)
    
    if ben_edu_val != -1:
        # map course min education
        course_edu_vals = filtered_df['minimum_education'].map(normalize_education).map(EDUCATION_ORDINAL).fillna(-1)
        # Keep courses where required education is <= beneficiary's education, or required is unknown
        filtered_df = filtered_df[(course_edu_vals <= ben_edu_val) | (course_edu_vals == -1)]

    # 3. Skill Filter
    ben_skill = beneficiary.get('existing_skill_level', 'Unknown')
    ben_skill_val = SKILL_ORDINAL.get(ben_skill, -1)
    
    if ben_skill_val != -1:
        course_skill_vals = filtered_df['required_skill_level'].map(SKILL_ORDINAL).fillna(-1)
        filtered_df = filtered_df[(course_skill_vals <= ben_skill_val) | (course_skill_vals == -1)]
        
    return filtered_df
