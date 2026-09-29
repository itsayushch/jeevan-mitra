import pandas as pd
import numpy as np
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def clean_beneficiary_data(input_path=None, output_path=None):
    if input_path is None:
        input_path = os.path.join(PROJECT_ROOT, 'data', 'raw', 'raw_beneficiary_data.csv')
    if output_path is None:
        output_path = os.path.join(PROJECT_ROOT, 'data', 'cleaned', 'cleaned_beneficiary_data.csv')
        
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    print(f"Initial shape: {df.shape}")
    print(f"Missing % per column:\n{(df.isnull().sum() / len(df)) * 100}")
    print(f"Exact duplicates count: {df.duplicated().sum()}")
    
    # 3. Exact duplicates
    df = df.drop_duplicates(subset='beneficiary_id', keep='first')
    
    # 5. Gender normalization
    def normalize_gender(x):
        if pd.isna(x):
            return 'Unknown'
        x_str = str(x).strip().lower()
        if x_str in ['male', 'm']:
            return 'Male'
        elif x_str in ['female', 'f']:
            return 'Female'
        else:
            return 'Other'
            
    if 'gender' in df.columns:
        df['gender'] = df['gender'].apply(normalize_gender)
        
    # 6. State normalization
    state_map = {
        'up': 'Uttar Pradesh', 'u.p.': 'Uttar Pradesh', 'u.p': 'Uttar Pradesh',
        'mp': 'Madhya Pradesh', 'm.p.': 'Madhya Pradesh',
        'wb': 'West Bengal', 'w.b.': 'West Bengal',
        'ap': 'Andhra Pradesh', 'a.p.': 'Andhra Pradesh',
        'tn': 'Tamil Nadu', 't.n.': 'Tamil Nadu',
        'jk': 'Jammu & Kashmir', 'j&k': 'Jammu & Kashmir',
        'hp': 'Himachal Pradesh', 'h.p.': 'Himachal Pradesh'
    }
    
    def normalize_state(x):
        if pd.isna(x):
            return 'Unknown'
        x_str = str(x).strip().lower()
        if x_str in state_map:
            return state_map[x_str]
        elif x_str:
            return x_str.title()
        return 'Unknown'
        
    if 'state' in df.columns:
        df['state'] = df['state'].apply(normalize_state)
        
    # 7. Education normalization
    edu_map = {
        'no formal': 'No_Formal', 'none': 'No_Formal', 'illiterate': 'No_Formal', 'no education': 'No_Formal',
        'primary': 'Primary', '5th': 'Primary', 'class 5': 'Primary', '1st-5th': 'Primary',
        'middle': 'Middle', '8th': 'Middle', 'class 8': 'Middle', '6th-8th': 'Middle',
        'secondary': 'Secondary', '10th': 'Secondary', 'class 10': 'Secondary', 'matric': 'Secondary', 'ssc': 'Secondary',
        'senior secondary': 'Senior_Secondary', '12th': 'Senior_Secondary', 'class 12': 'Senior_Secondary', 'intermediate': 'Senior_Secondary', 'hsc': 'Senior_Secondary', '+2': 'Senior_Secondary', 'puc': 'Senior_Secondary',
        'graduate': 'Graduate', 'graduation': 'Graduate', 'b.a.': 'Graduate', 'ba': 'Graduate', 'b.sc': 'Graduate', 'bsc': 'Graduate', 'b.com': 'Graduate', 'bcom': 'Graduate', 'b.tech': 'Graduate', 'btech': 'Graduate', 'degree': 'Graduate',
        'post graduate': 'Post_Graduate', 'post_graduate': 'Post_Graduate', 'pg': 'Post_Graduate', 'm.a.': 'Post_Graduate', 'ma': 'Post_Graduate', 'm.sc': 'Post_Graduate', 'msc': 'Post_Graduate', 'm.tech': 'Post_Graduate', 'mtech': 'Post_Graduate', 'masters': 'Post_Graduate'
    }
    
    def normalize_edu(x):
        if pd.isna(x):
            return 'Unknown'
        x_str = str(x).strip().lower()
        return edu_map.get(x_str, 'Unknown')
        
    if 'education_level' in df.columns:
        df['education_level'] = df['education_level'].apply(normalize_edu)
        
    # 8. Rural/Urban normalization
    def normalize_ru(x):
        if pd.isna(x):
            return 'Unknown'
        x_str = str(x).strip().lower()
        if x_str == 'rural': return 'Rural'
        if x_str == 'urban': return 'Urban'
        if x_str in ['semi-urban', 'semi urban', 'peri-urban']: return 'Semi-Urban'
        return 'Unknown'
        
    if 'rural_urban' in df.columns:
        df['rural_urban'] = df['rural_urban'].apply(normalize_ru)
        
    # 9. Career interest normalization
    career_map = {
        'it': 'IT / ITES', 'i.t.': 'IT / ITES', 'information technology': 'IT / ITES', 'computers': 'IT / ITES', 'software': 'IT / ITES', 'coding': 'IT / ITES',
        'health': 'Healthcare', 'healthcare': 'Healthcare', 'medical': 'Healthcare', 'nursing': 'Healthcare', 'pharma': 'Healthcare',
        'farming': 'Agriculture', 'agriculture': 'Agriculture', 'agri': 'Agriculture', 'kisan': 'Agriculture',
        'hotel': 'Hospitality', 'hospitality': 'Hospitality', 'food service': 'Hospitality'
    }
    
    def normalize_career(x):
        if pd.isna(x):
            return 'Unknown'
        x_str = str(x).strip().lower()
        return career_map.get(x_str, 'Unknown')
        
    if 'career_interest' in df.columns:
        df['career_interest'] = df['career_interest'].apply(normalize_career)
        
    # 10. Employment status
    if 'employment_status' in df.columns:
        df['employment_status'] = df['employment_status'].fillna('Unknown').astype(str).str.strip().str.title()
        
    # 11. Social category
    def normalize_social(x):
        if pd.isna(x):
            return 'Unknown'
        x_str = str(x).strip().upper()
        if x_str in ['GENERAL', 'GEN']: return 'General'
        if x_str == 'OBC': return 'OBC'
        if x_str == 'SC': return 'SC'
        if x_str == 'ST': return 'ST'
        return x_str
        
    if 'social_category' in df.columns:
        df['social_category'] = df['social_category'].apply(normalize_social)
        
    # 12. Existing skill level
    if 'existing_skill_level' in df.columns:
        def norm_skill(x):
            if pd.isna(x): return 'Beginner'
            x_str = str(x).strip().title()
            if x_str in ['Beginner', 'Intermediate', 'Advanced', 'Expert']:
                return x_str
            return 'Beginner'
        df['existing_skill_level'] = df['existing_skill_level'].apply(norm_skill)
        
    # 13. Numerical invalid value handling
    if 'age' in df.columns:
        df['age'] = pd.to_numeric(df['age'], errors='coerce')
        df.loc[(df['age'] <= 0) | (df['age'] > 100), 'age'] = np.nan
        df['age'] = df['age'].fillna(df['age'].median())
        
    if 'annual_family_income' in df.columns:
        df['annual_family_income'] = pd.to_numeric(df['annual_family_income'], errors='coerce')
        df.loc[df['annual_family_income'] < 0, 'annual_family_income'] = np.nan
        df.loc[df['annual_family_income'] > 5000000, 'annual_family_income'] = 5000000
        df['annual_family_income'] = df['annual_family_income'].fillna(df['annual_family_income'].median())
        
    if 'work_experience_years' in df.columns:
        df['work_experience_years'] = pd.to_numeric(df['work_experience_years'], errors='coerce')
        df.loc[df['work_experience_years'] < 0, 'work_experience_years'] = np.nan
        df.loc[df['work_experience_years'] > 50, 'work_experience_years'] = 50
        df['work_experience_years'] = df['work_experience_years'].fillna(df['work_experience_years'].median())
        
    skill_cols = ['digital_literacy', 'communication_skill', 'numerical_skill', 'technical_skill', 'entrepreneurial_skill']
    for col in skill_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].clip(1, 10)
            df[col] = df[col].fillna(df[col].median()).round().astype(int)
            
    state_lat_lon = {
        'Uttar Pradesh': (26.8467, 80.9462),
        'Madhya Pradesh': (22.9734, 78.6569),
        'Maharashtra': (19.7515, 75.7139),
        'Bihar': (25.0961, 85.3131),
        'West Bengal': (22.9868, 87.8550),
        'Andhra Pradesh': (15.9129, 79.7400),
        'Tamil Nadu': (11.1271, 78.6569),
        'Rajasthan': (27.0238, 74.2179),
        'Karnataka': (15.3173, 75.7139),
        'Gujarat': (22.2587, 71.1924)
    }
    
    if 'latitude' in df.columns:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df.loc[(df['latitude'] < 6) | (df['latitude'] > 38), 'latitude'] = np.nan
    if 'longitude' in df.columns:
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df.loc[(df['longitude'] < 67) | (df['longitude'] > 98), 'longitude'] = np.nan
        
    def impute_lat(row):
        if pd.isna(row['latitude']) and row['state'] in state_lat_lon:
            return state_lat_lon[row['state']][0]
        return row['latitude']
    
    def impute_lon(row):
        if pd.isna(row['longitude']) and row['state'] in state_lat_lon:
            return state_lat_lon[row['state']][1]
        return row['longitude']
        
    if 'latitude' in df.columns and 'state' in df.columns:
        df['latitude'] = df.apply(impute_lat, axis=1)
        df['latitude'] = df['latitude'].fillna(20.5937) 
    if 'longitude' in df.columns and 'state' in df.columns:
        df['longitude'] = df.apply(impute_lon, axis=1)
        df['longitude'] = df['longitude'].fillna(78.9629)
        
    if 'distance_to_training_center_km' in df.columns:
        df['distance_to_training_center_km'] = pd.to_numeric(df['distance_to_training_center_km'], errors='coerce')
        df.loc[df['distance_to_training_center_km'] < 0, 'distance_to_training_center_km'] = np.nan
        df.loc[df['distance_to_training_center_km'] > 500, 'distance_to_training_center_km'] = 500
        df['distance_to_training_center_km'] = df['distance_to_training_center_km'].fillna(df['distance_to_training_center_km'].median())
        
    if 'previous_training_count' in df.columns:
        df['previous_training_count'] = pd.to_numeric(df['previous_training_count'], errors='coerce')
        df.loc[df['previous_training_count'] < 0, 'previous_training_count'] = np.nan
        df['previous_training_count'] = df['previous_training_count'].fillna(0)
        
    if 'training_completion_rate' in df.columns:
        df['training_completion_rate'] = pd.to_numeric(df['training_completion_rate'], errors='coerce')
        df['training_completion_rate'] = df['training_completion_rate'].clip(0, 1)
        df['training_completion_rate'] = df['training_completion_rate'].fillna(0.0)

    # 14. Categorical missing value handling
    cat_fills = {
        'gender': 'Unknown',
        'state': 'Unknown',
        'education_level': df['education_level'].mode()[0] if 'education_level' in df.columns and not df['education_level'].mode().empty else 'Unknown',
        'employment_status': df['employment_status'].mode()[0] if 'employment_status' in df.columns and not df['employment_status'].mode().empty else 'Unknown',
        'career_interest': 'Unknown',
        'preferred_language': 'Hindi',
        'existing_skill_level': 'Beginner'
    }
    
    for col, fill_val in cat_fills.items():
        if col in df.columns:
            df[col] = df[col].fillna(fill_val)
            
    for col in df.select_dtypes(include=['object', 'category']).columns:
        df[col] = df[col].fillna('Unknown')
        
    # 15. Numerical missing value handling
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].fillna(df[col].median() if not df[col].dropna().empty else 0)
        
    # 16. Final validation
    print(f"Remaining NaNs: {df.isnull().sum().sum()}")
    print(f"Final shape: {df.shape}")
    
    # 17. Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved cleaned data to {output_path}")
    
    return df

def generate_cleaning_report(raw_df, cleaned_df):
    return {
        'raw_shape': raw_df.shape,
        'cleaned_shape': cleaned_df.shape,
        'raw_duplicates': raw_df.duplicated().sum(),
        'cleaned_duplicates': cleaned_df.duplicated().sum(),
        'raw_missing': raw_df.isnull().sum().to_dict(),
        'cleaned_missing': cleaned_df.isnull().sum().to_dict()
    }

if __name__ == '__main__':
    clean_beneficiary_data()
