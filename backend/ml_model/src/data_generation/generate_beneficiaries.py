import os
import pandas as pd
import numpy as np
import random
import string

# ==========================================
# SYNTHETIC DATA GENERATION SCRIPT
# ALL DATA GENERATED IS STRICTLY SYNTHETIC
# ==========================================

def inject_missing(series, prob):
    mask = np.random.rand(len(series)) < prob
    series.loc[mask] = np.nan
    return series

def inject_messy_case(series):
    def mess_up(x):
        if pd.isna(x): return x
        x = str(x)
        r = random.random()
        if r < 0.2: return x.lower()
        if r < 0.4: return x.upper()
        if r < 0.5: return " " + x + " "
        return x
    return series.apply(mess_up)

def generate_beneficiaries(n=10000, seed=42):
    np.random.seed(seed)
    random.seed(seed)
    
    beneficiary_ids = [f"BEN_{i:05d}" for i in range(1, n + 1)]
    
    # Skewed age distribution
    ages = np.random.gamma(shape=2.5, scale=6.0, size=n) + 14
    ages = ages.astype(int)
    
    # Messy gender
    genders_pool = ['Male', 'Female', 'Other']
    genders = np.random.choice(genders_pool, size=n, p=[0.55, 0.43, 0.02])
    
    states_pool = ['Uttar Pradesh', 'Bihar', 'Madhya Pradesh', 'Maharashtra', 'Rajasthan', 'West Bengal']
    states = np.random.choice(states_pool, size=n, p=[0.25, 0.2, 0.15, 0.15, 0.15, 0.1])
    districts = [f"{s} District {random.randint(1, 10)}" for s in states]
    
    rural_urban = np.random.choice(['Rural', 'Urban', 'Semi-Urban'], size=n, p=[0.65, 0.25, 0.10])
    social_categories = np.random.choice(['General', 'OBC', 'SC', 'ST', 'Minority'], size=n, p=[0.20, 0.40, 0.20, 0.10, 0.10])
    
    edu_levels = ['No_Formal', 'Primary', 'Middle', 'Secondary', 'Senior_Secondary', 'Graduate', 'Post_Graduate']
    education = np.random.choice(edu_levels, size=n, p=[0.1, 0.15, 0.2, 0.25, 0.15, 0.1, 0.05])
    edu_stream = np.random.choice(['Science', 'Commerce', 'Arts', 'Vocational', 'Not_Applicable'], size=n)
    
    # Income right skewed
    incomes = np.random.lognormal(mean=11.5, sigma=1.0, size=n)
    
    emp_status = np.random.choice(['Unemployed', 'Self_Employed', 'Wage_Worker', 'Student', 'Homemaker'], size=n, p=[0.4, 0.2, 0.15, 0.15, 0.1])
    occupations = ['Farmer', 'Daily Wage Worker', 'Shop Helper', 'Student', 'Homemaker', 'None', 'Clerk']
    current_occupation = [random.choice(occupations) if e != 'Unemployed' else 'None' for e in emp_status]
    
    exp_years = np.clip(np.random.normal(loc=ages-18, scale=5), 0, 40).astype(int)
    
    dig_lit = np.clip(np.random.normal(loc=5, scale=2), 1, 10).astype(int)
    comm_skill = np.clip(np.random.normal(loc=5, scale=2), 1, 10).astype(int)
    num_skill = np.clip(np.random.normal(loc=5, scale=2), 1, 10).astype(int)
    tech_skill = np.clip(np.random.normal(loc=5, scale=2), 1, 10).astype(int)
    ent_skill = np.clip(np.random.normal(loc=5, scale=2), 1, 10).astype(int)
    
    existing_skill = np.random.choice(['Beginner', 'Intermediate', 'Advanced', 'Expert'], size=n)
    
    sectors = [
        'IT / ITES', 'Healthcare', 'Retail', 'Agriculture', 'Construction', 
        'Automotive', 'Electronics', 'Tourism', 'Hospitality', 'Banking / Finance', 
        'Beauty & Wellness', 'Logistics', 'Manufacturing', 'Green Jobs', 'Telecom', 'Entrepreneurship'
    ]
    career_interest = np.random.choice(sectors, size=n)
    pref_occ = [f"{ci} Role" for ci in career_interest]
    pref_ind = career_interest.copy()
    pref_work = np.random.choice(['Full_Time', 'Part_Time', 'Freelance', 'Seasonal'], size=n)
    pref_mode = np.random.choice(['Online', 'Offline', 'Blended'], size=n)
    pref_lang = np.random.choice(['Hindi', 'English', 'Tamil', 'Telugu', 'Bengali'], size=n)
    
    lat = np.random.uniform(8, 37, n)
    lon = np.random.uniform(68, 97, n)
    distance_km = np.random.gamma(2, 20, n)
    
    tc_avail = np.where(distance_km < 10, 'Yes', np.where(distance_km < 50, 'Limited', 'No'))
    local_demand = np.random.choice(['Low', 'Medium', 'High'], size=n)
    local_industry = np.random.choice(sectors, size=n)
    
    prev_train = np.random.choice(['Yes', 'No'], size=n, p=[0.3, 0.7])
    prev_train_cnt = np.where(prev_train == 'Yes', np.random.randint(1, 5, n), 0)
    train_comp_rate = np.where(prev_train == 'Yes', np.random.uniform(0.3, 1.0, n), 0.0)
    
    pref_dur = np.random.choice(['Short', 'Medium', 'Long'], size=n)
    
    df = pd.DataFrame({
        'beneficiary_id': beneficiary_ids,
        'age': ages,
        'gender': genders,
        'state': states,
        'district': districts,
        'rural_urban': rural_urban,
        'social_category': social_categories,
        'education_level': education,
        'education_stream': edu_stream,
        'annual_family_income': incomes,
        'employment_status': emp_status,
        'current_occupation': current_occupation,
        'work_experience_years': exp_years,
        'digital_literacy': dig_lit,
        'communication_skill': comm_skill,
        'numerical_skill': num_skill,
        'technical_skill': tech_skill,
        'entrepreneurial_skill': ent_skill,
        'existing_skill_level': existing_skill,
        'career_interest': career_interest,
        'preferred_occupation': pref_occ,
        'preferred_industry': pref_ind,
        'preferred_work_type': pref_work,
        'preferred_training_mode': pref_mode,
        'preferred_language': pref_lang,
        'latitude': lat,
        'longitude': lon,
        'distance_to_training_center_km': distance_km,
        'training_center_availability': tc_avail,
        'local_job_demand': local_demand,
        'local_industry': local_industry,
        'previous_training': prev_train,
        'previous_training_count': prev_train_cnt,
        'training_completion_rate': train_comp_rate,
        'preferred_duration': pref_dur
    })
    
    # DATA QUALITY ISSUES INJECTION
    
    # 1. Invalid numerics (1% age, 2% income, outliers)
    idx = np.random.choice(n, int(n * 0.01), replace=False)
    df.loc[idx, 'age'] = np.random.choice([-1, -5, 120, 150, np.nan], len(idx))
    
    idx = np.random.choice(n, int(n * 0.02), replace=False)
    df.loc[idx, 'annual_family_income'] = np.random.choice([-5000, 50000000, np.nan], len(idx))
    
    # 2. Messy Strings (Inconsistent case)
    string_cols = ['gender', 'state', 'rural_urban', 'education_level', 'career_interest']
    for col in string_cols:
        df[col] = inject_messy_case(df[col])
        
    # Additional specific variants
    df.loc[np.random.choice(n, int(n*0.02)), 'education_level'] = '10th'
    df.loc[np.random.choice(n, int(n*0.02)), 'education_level'] = 'B.A.'
    df.loc[np.random.choice(n, int(n*0.05)), 'career_interest'] = 'IT'
    df.loc[np.random.choice(n, int(n*0.02)), 'career_interest'] = 'I.T.'
    df.loc[np.random.choice(n, int(n*0.02)), 'gender'] = 'M'
    df.loc[np.random.choice(n, int(n*0.02)), 'gender'] = 'F'
    
    # 3. Missing values (~5-15%)
    df['annual_family_income'] = inject_missing(df['annual_family_income'], 0.08)
    df['career_interest'] = inject_missing(df['career_interest'], 0.05)
    df['age'] = inject_missing(df['age'], 0.02)
    df['education_stream'] = inject_missing(df['education_stream'], 0.10)
    
    # 4. Out of range skills
    idx = np.random.choice(n, int(n * 0.01), replace=False)
    df.loc[idx, 'digital_literacy'] = 15
    df.loc[idx, 'technical_skill'] = 0
    
    # 5. Duplicates
    duplicates = df.sample(200, replace=True)
    df = pd.concat([df, duplicates], ignore_index=True)
    
    # Near duplicates
    near_dupes = df.sample(50).copy()
    near_dupes['age'] = near_dupes['age'] + 1
    near_dupes['annual_family_income'] = near_dupes['annual_family_income'] * 1.05
    df = pd.concat([df, near_dupes], ignore_index=True)
    
    # Shuffle
    df = df.sample(frac=1).reset_index(drop=True)
    
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    save_path = os.path.join(PROJECT_ROOT, 'data', 'raw', 'raw_beneficiary_data.csv')
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    df.to_csv(save_path, index=False)
    print(f"Generated {len(df)} synthetic beneficiary records with noise and saved to {save_path}")

if __name__ == '__main__':
    generate_beneficiaries()
