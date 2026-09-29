import os
import numpy as np
import pandas as pd
import math


def compute_pair_features(beneficiary_row, course_row) -> dict:
    """Computes engineered features for a single (beneficiary, course) pair."""
    features = {}

    # ==========================================================
    # 1. SKILL MATCH SCORE
    # ==========================================================

    b_skills = {
        'digital': float(beneficiary_row.get('digital_literacy', 0) or 0) / 10.0,
        'communication': float(beneficiary_row.get('communication_skill', 0) or 0) / 10.0,
        'numerical': float(beneficiary_row.get('numerical_skill', 0) or 0) / 10.0,
        'technical': float(beneficiary_row.get('technical_skill', 0) or 0) / 10.0,
        'entrepreneurial': float(beneficiary_row.get('entrepreneurial_skill', 0) or 0) / 10.0
    }

    sector = str(course_row.get('sector', '')).strip()
    sector_lower = sector.lower()

    # IT / ITES
    if sector_lower in [
        'it',
        'it / ites',
        'ites',
        'information technology'
    ]:
        weights = {
            'digital': 0.40,
            'technical': 0.30,
            'numerical': 0.20,
            'communication': 0.05,
            'entrepreneurial': 0.05
        }

    # Healthcare
    elif sector_lower in [
        'healthcare',
        'health care',
        'medical'
    ]:
        weights = {
            'communication': 0.30,
            'numerical': 0.20,
            'technical': 0.30,
            'digital': 0.10,
            'entrepreneurial': 0.10
        }

    # Agriculture
    elif sector_lower in [
        'agriculture',
        'agri',
        'farming'
    ]:
        weights = {
            'technical': 0.30,
            'numerical': 0.20,
            'entrepreneurial': 0.20,
            'digital': 0.10,
            'communication': 0.20
        }

    # Retail
    elif sector_lower == 'retail':
        weights = {
            'communication': 0.40,
            'digital': 0.20,
            'numerical': 0.20,
            'entrepreneurial': 0.15,
            'technical': 0.05
        }

    # Construction
    elif sector_lower == 'construction':
        weights = {
            'technical': 0.50,
            'numerical': 0.20,
            'communication': 0.10,
            'digital': 0.10,
            'entrepreneurial': 0.10
        }

    # Other sectors
    else:
        weights = {
            'digital': 0.20,
            'communication': 0.20,
            'numerical': 0.20,
            'technical': 0.20,
            'entrepreneurial': 0.20
        }

    skill_match_score = sum(
        b_skills.get(key, 0) * weights.get(key, 0)
        for key in weights
    )

    features['skill_match_score'] = skill_match_score

    # ==========================================================
    # 2. EDUCATION ELIGIBILITY
    # ==========================================================

    edu_map = {
        'No_Formal': 0,
        'Primary': 1,
        'Middle': 2,
        'Secondary': 3,
        'Senior_Secondary': 4,
        'Graduate': 5,
        'Post_Graduate': 6
    }

    b_edu = str(
        beneficiary_row.get('education_level', 'Middle')
    ).strip()

    b_edu_val = edu_map.get(b_edu, 2)

    c_edu = str(
        course_row.get('minimum_education', 'No_Formal')
    ).strip()

    c_edu_val = edu_map.get(c_edu, 0)

    features['education_eligibility'] = (
        1 if b_edu_val >= c_edu_val else 0
    )

    # ==========================================================
    # 3. CAREER INTEREST MATCH
    # ==========================================================

    b_career = str(
        beneficiary_row.get('career_interest', '')
    ).strip().lower()

    c_sector = sector_lower

    career_match = False

    if b_career and c_sector:

        if b_career == c_sector:
            career_match = True

        elif b_career in c_sector or c_sector in b_career:
            career_match = True

        else:
            career_aliases = {
                'it / ites': [
                    'it',
                    'ites',
                    'information technology'
                ],
                'it': [
                    'it / ites',
                    'ites',
                    'information technology'
                ],
                'information technology': [
                    'it',
                    'it / ites',
                    'ites'
                ],
                'healthcare': [
                    'health care',
                    'medical'
                ],
                'agriculture': [
                    'agri',
                    'farming'
                ],
                'banking / finance': [
                    'banking',
                    'finance'
                ],
                'beauty & wellness': [
                    'beauty',
                    'wellness'
                ]
            }

            if c_sector in career_aliases.get(b_career, []):
                career_match = True

    features['career_interest_match'] = (
        1 if career_match else 0
    )

    # ==========================================================
    # 4. INDUSTRY MATCH
    # ==========================================================

    b_industry = str(
        beneficiary_row.get('preferred_industry', '')
    ).strip().lower()

    c_industry = str(
        course_row.get('industry', '')
    ).strip().lower()

    industry_match = False

    if b_industry and c_industry:

        if b_industry == c_industry:
            industry_match = True

        elif b_industry in c_industry or c_industry in b_industry:
            industry_match = True

    features['industry_match'] = (
        1 if industry_match else 0
    )

    # ==========================================================
    # 5. OCCUPATION MATCH
    # ==========================================================

    preferred_occupation = str(
        beneficiary_row.get('preferred_occupation', '')
    ).strip().lower()

    job_role = str(
        course_row.get('job_role', '')
    ).strip().lower()

    course_name = str(
        course_row.get('course_name', '')
    ).strip().lower()

    occupation_match = False

    if preferred_occupation:

        if preferred_occupation == job_role:
            occupation_match = True

        elif preferred_occupation in job_role:
            occupation_match = True

        elif preferred_occupation in course_name:
            occupation_match = True

    features['occupation_match'] = (
        1 if occupation_match else 0
    )

    # ==========================================================
    # 6. LOCAL DEMAND SCORE
    # ==========================================================

    demand_map = {
        'Low': 0.25,
        'Medium': 0.50,
        'High': 0.75,
        'Very_High': 1.00
    }

    b_demand = demand_map.get(
        str(
            beneficiary_row.get(
                'local_job_demand',
                ''
            )
        ).strip(),
        0.5
    )

    c_demand = demand_map.get(
        str(
            course_row.get(
                'local_demand',
                ''
            )
        ).strip(),
        0.5
    )

    features['local_demand_score'] = (
        b_demand * c_demand
    )

    # ==========================================================
    # 7. DISTANCE PENALTY
    # ==========================================================

    mode = str(
        course_row.get('delivery_mode', '')
    ).strip().lower()

    if mode == 'online':

        features['distance_penalty'] = 1.0

    else:

        try:
            dist = float(
                beneficiary_row.get(
                    'distance_to_training_center_km',
                    0
                ) or 0
            )
        except (TypeError, ValueError):
            dist = 0.0

        if pd.isna(dist):
            dist = 0.0

        features['distance_penalty'] = (
            1.0 / (1.0 + dist / 50.0)
        )

    # ==========================================================
    # 8. LANGUAGE MATCH
    # ==========================================================

    b_lang = str(
        beneficiary_row.get(
            'preferred_language',
            ''
        )
    ).strip().lower()

    c_lang = str(
        course_row.get(
            'language',
            ''
        )
    ).strip().lower()

    if b_lang and c_lang:

        c_langs = [
            language.strip()
            for language in c_lang.split(',')
        ]

        features['language_match'] = (
            1 if b_lang in c_langs else 0
        )

    else:

        features['language_match'] = 0

    # ==========================================================
    # 9. AGE ELIGIBILITY
    # ==========================================================

    try:
        b_age = float(
            beneficiary_row.get(
                'age',
                0
            ) or 0
        )
    except (TypeError, ValueError):
        b_age = 0

    if pd.isna(b_age):
        b_age = 0

    try:
        c_age_min = float(
            course_row.get(
                'age_min',
                0
            ) or 0
        )
    except (TypeError, ValueError):
        c_age_min = 0

    try:
        c_age_max = float(
            course_row.get(
                'age_max',
                100
            ) or 100
        )
    except (TypeError, ValueError):
        c_age_max = 100

    if pd.isna(c_age_min):
        c_age_min = 0

    if pd.isna(c_age_max):
        c_age_max = 100

    features['age_eligibility'] = (
        1
        if c_age_min <= b_age <= c_age_max
        else 0
    )

    # ==========================================================
    # 10. TRAINING MODE MATCH
    # ==========================================================

    b_mode = str(
        beneficiary_row.get(
            'preferred_training_mode',
            ''
        )
    ).strip().lower()

    if b_mode == 'blended' or mode == 'blended':

        features['training_mode_match'] = 1

    else:

        features['training_mode_match'] = (
            1 if b_mode == mode else 0
        )

    # ==========================================================
    # 11. NSQF APPROPRIATENESS
    # ==========================================================

    expected_nsqf_map = {
        0: 1,
        1: 2,
        2: 3,
        3: 4,
        4: 5,
        5: 6.5,
        6: 8.5
    }

    b_expected_nsqf = expected_nsqf_map.get(
        b_edu_val,
        3
    )

    try:
        c_nsqf = float(
            course_row.get(
                'nsqf_level',
                3
            ) or 3
        )
    except (TypeError, ValueError):
        c_nsqf = 3

    if pd.isna(c_nsqf):
        c_nsqf = 3

    features['nsqf_appropriateness'] = math.exp(
        -0.5 *
        ((c_nsqf - b_expected_nsqf) / 2.0) ** 2
    )

    # ==========================================================
    # 12. EXPERIENCE RELEVANCE
    # ==========================================================

    try:
        exp = float(
            beneficiary_row.get(
                'work_experience_years',
                0
            ) or 0
        )
    except (TypeError, ValueError):
        exp = 0

    if pd.isna(exp):
        exp = 0

    exp_rel = (
        math.log1p(exp) *
        features['career_interest_match']
    ) / 3.0

    features['experience_relevance'] = min(
        exp_rel,
        1.0
    )

    return features


def create_training_dataset(
    beneficiaries_df,
    courses_df,
    interactions_df,
    negative_ratio=3,
    seed=42
) -> pd.DataFrame:

    np.random.seed(seed)

    # ==========================================================
    # BENEFICIARY COLUMNS
    # ==========================================================

    b_cols = [
        'beneficiary_id',
        'age',
        'gender',
        'state',
        'district',
        'rural_urban',
        'social_category',
        'education_level',
        'education_stream',
        'annual_family_income',
        'employment_status',
        'current_occupation',
        'work_experience_years',
        'digital_literacy',
        'communication_skill',
        'numerical_skill',
        'technical_skill',
        'entrepreneurial_skill',
        'existing_skill_level',
        'career_interest',
        'preferred_work_type',
        'preferred_training_mode',
        'preferred_language',
        'distance_to_training_center_km',
        'local_job_demand',
        'local_industry',
        'previous_training_count',
        'training_completion_rate',
        'preferred_duration'
    ]

    if (
        'preferred_industry' not in b_cols
        and 'preferred_industry' in beneficiaries_df.columns
    ):
        b_cols.append('preferred_industry')

    if (
        'preferred_occupation' not in b_cols
        and 'preferred_occupation' in beneficiaries_df.columns
    ):
        b_cols.append('preferred_occupation')

    # ==========================================================
    # COURSE COLUMNS
    # ==========================================================

    c_cols = [
        'course_id',
        'nsqf_level',
        'sector',
        'course_duration_hours',
        'required_skill_level',
        'delivery_mode',
        'average_salary',
        'local_demand'
    ]

    c_eval_cols = [
        'minimum_education',
        'industry',
        'language',
        'age_min',
        'age_max',
        'job_role',
        'course_name'
    ]

    for c in c_eval_cols:

        if (
            c not in c_cols
            and c in courses_df.columns
        ):
            c_cols.append(c)

    # ==========================================================
    # DICTIONARIES
    # ==========================================================

    b_dict = (
        beneficiaries_df
        .set_index('beneficiary_id')
        .to_dict('index')
    )

    c_dict = (
        courses_df
        .set_index('course_id')
        .to_dict('index')
    )

    course_ids = list(
        courses_df['course_id'].unique()
    )

    data_rows = []

    # ==========================================================
    # CREATE POSITIVE + NEGATIVE PAIRS
    # ==========================================================

    grouped = interactions_df.groupby(
        'beneficiary_id'
    )

    for b_id, group in grouped:

        if b_id not in b_dict:
            continue

        b_row = b_dict[b_id]

        interacted_courses = set(
            group['course_id']
        )

        # ------------------------------------------------------
        # Positive samples
        # ------------------------------------------------------

        for _, row in group.iterrows():

            c_id = row['course_id']

            if c_id not in c_dict:
                continue

            c_row = c_dict[c_id]

            features = compute_pair_features(
                b_row,
                c_row
            )

            row_data = {
                'beneficiary_id': b_id,
                'course_id': c_id,
                'outcome': row['outcome']
            }

            for c in b_cols:

                if c != 'beneficiary_id':

                    row_data[c] = b_row.get(
                        c,
                        np.nan
                    )

            for c in c_cols:

                if c != 'course_id':

                    row_data[c] = c_row.get(
                        c,
                        np.nan
                    )

            row_data.update(features)

            data_rows.append(row_data)

        # ------------------------------------------------------
        # Negative samples
        # ------------------------------------------------------

        available_negatives = [
            c
            for c in course_ids
            if c not in interacted_courses
        ]

        if not available_negatives:
            continue

        n_samples = min(
            negative_ratio,
            len(available_negatives)
        )

        neg_samples = np.random.choice(
            available_negatives,
            size=n_samples,
            replace=False
        )

        for c_id in neg_samples:

            if c_id not in c_dict:
                continue

            c_row = c_dict[c_id]

            features = compute_pair_features(
                b_row,
                c_row
            )

            row_data = {
                'beneficiary_id': b_id,
                'course_id': c_id,
                'outcome': 0
            }

            for c in b_cols:

                if c != 'beneficiary_id':

                    row_data[c] = b_row.get(
                        c,
                        np.nan
                    )

            for c in c_cols:

                if c != 'course_id':

                    row_data[c] = c_row.get(
                        c,
                        np.nan
                    )

            row_data.update(features)

            data_rows.append(row_data)

    final_df = pd.DataFrame(
        data_rows
    )

    # ==========================================================
    # FINAL COLUMN ORDER
    # ==========================================================

    out_b_cols = [
        'beneficiary_id',
        'age',
        'gender',
        'state',
        'district',
        'rural_urban',
        'social_category',
        'education_level',
        'education_stream',
        'annual_family_income',
        'employment_status',
        'current_occupation',
        'work_experience_years',
        'digital_literacy',
        'communication_skill',
        'numerical_skill',
        'technical_skill',
        'entrepreneurial_skill',
        'existing_skill_level',
        'career_interest',
        'preferred_work_type',
        'preferred_training_mode',
        'preferred_language',
        'distance_to_training_center_km',
        'local_job_demand',
        'local_industry',
        'previous_training_count',
        'training_completion_rate',
        'preferred_duration'
    ]

    if 'preferred_industry' in final_df.columns:
        out_b_cols.append(
            'preferred_industry'
        )

    if 'preferred_occupation' in final_df.columns:
        out_b_cols.append(
            'preferred_occupation'
        )

    out_c_cols = [
        'course_id',
        'nsqf_level',
        'sector',
        'course_duration_hours',
        'required_skill_level',
        'delivery_mode',
        'average_salary',
        'local_demand',
        'minimum_education',
        'industry',
        'language',
        'age_min',
        'age_max',
        'job_role',
        'course_name'
    ]

    engineered = [
        'skill_match_score',
        'education_eligibility',
        'career_interest_match',
        'industry_match',
        'occupation_match',
        'local_demand_score',
        'distance_penalty',
        'language_match',
        'age_eligibility',
        'training_mode_match',
        'nsqf_appropriateness',
        'experience_relevance'
    ]

    final_cols = (
        out_b_cols
        + out_c_cols
        + engineered
        + ['outcome']
    )

    for col in final_cols:

        if col not in final_df.columns:

            final_df[col] = np.nan

    final_df = final_df[
        final_cols
    ]

    # ==========================================================
    # SAVE
    # ==========================================================

    PROJECT_ROOT = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )

    processed_dir = os.path.join(
        PROJECT_ROOT,
        'data',
        'processed'
    )

    os.makedirs(
        processed_dir,
        exist_ok=True
    )

    final_df.to_csv(
        os.path.join(
            processed_dir,
            'processed_beneficiary_data.csv'
        ),
        index=False
    )

    return final_df


if __name__ == '__main__':
    pass