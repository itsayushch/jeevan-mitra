import os
import pandas as pd
import numpy as np
import random

# ==========================================
# SYNTHETIC DATA GENERATION SCRIPT
# ALL DATA GENERATED IS STRICTLY SYNTHETIC
# ==========================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)


def clean_str(s):
    if pd.isna(s):
        return ""

    s = str(s).lower().strip()

    # Common aliases
    aliases = {
        'it': 'it / ites',
        'i.t.': 'it / ites',
        'information technology': 'it / ites',
        'ites': 'it / ites',

        'm': 'male',
        'male': 'male',

        'f': 'female',
        'female': 'female',

        'b.a.': 'graduate',
        'graduation': 'graduate',

        '10th': 'secondary',
        'class 10': 'secondary'
    }

    return aliases.get(s, s)


def normalize_text(s):
    """
    Normalizes text for approximate matching.
    """
    if pd.isna(s):
        return ""

    s = str(s).lower().strip()

    replacements = {
        '/': ' ',
        '-': ' ',
        '_': ' ',
        '&': ' and ',
        ',': ' '
    }

    for old, new in replacements.items():
        s = s.replace(old, new)

    return " ".join(s.split())


def text_match(value1, value2):
    """
    Flexible text matching.
    """
    a = normalize_text(value1)
    b = normalize_text(value2)

    if not a or not b:
        return False

    if a == b:
        return True

    if a in b or b in a:
        return True

    return False


def calculate_skill_match(b, c):
    """
    Calculates approximate beneficiary-course skill compatibility.
    """

    digital = float(b.get('digital_literacy', 0) or 0) / 10.0
    communication = float(
        b.get('communication_skill', 0) or 0
    ) / 10.0

    numerical = float(
        b.get('numerical_skill', 0) or 0
    ) / 10.0

    technical = float(
        b.get('technical_skill', 0) or 0
    ) / 10.0

    entrepreneurial = float(
        b.get('entrepreneurial_skill', 0) or 0
    ) / 10.0

    sector = normalize_text(
        c.get('sector', '')
    )

    # --------------------------------------------------
    # IT / ITES
    # --------------------------------------------------

    if (
        'it ites' in sector
        or sector == 'it'
        or 'information technology' in sector
    ):

        skill_score = (
            digital * 0.40
            + technical * 0.30
            + numerical * 0.20
            + communication * 0.05
            + entrepreneurial * 0.05
        )

    # --------------------------------------------------
    # Healthcare
    # --------------------------------------------------

    elif (
        'healthcare' in sector
        or 'health care' in sector
        or 'medical' in sector
    ):

        skill_score = (
            communication * 0.30
            + numerical * 0.20
            + technical * 0.30
            + digital * 0.10
            + entrepreneurial * 0.10
        )

    # --------------------------------------------------
    # Agriculture
    # --------------------------------------------------

    elif (
        'agriculture' in sector
        or 'farming' in sector
        or 'agri' in sector
    ):

        skill_score = (
            technical * 0.30
            + numerical * 0.20
            + entrepreneurial * 0.20
            + digital * 0.10
            + communication * 0.20
        )

    # --------------------------------------------------
    # Retail
    # --------------------------------------------------

    elif 'retail' in sector:

        skill_score = (
            communication * 0.40
            + digital * 0.20
            + numerical * 0.20
            + entrepreneurial * 0.15
            + technical * 0.05
        )

    # --------------------------------------------------
    # Construction
    # --------------------------------------------------

    elif 'construction' in sector:

        skill_score = (
            technical * 0.50
            + numerical * 0.20
            + communication * 0.10
            + digital * 0.10
            + entrepreneurial * 0.10
        )

    # --------------------------------------------------
    # Other sectors
    # --------------------------------------------------

    else:

        skill_score = (
            digital * 0.20
            + communication * 0.20
            + numerical * 0.20
            + technical * 0.20
            + entrepreneurial * 0.20
        )

    return float(
        np.clip(skill_score, 0, 1)
    )


def generate_interactions(
    beneficiaries_path=None,
    courses_path=None,
    n_interactions=25000,
    seed=42
):

    if beneficiaries_path is None:

        beneficiaries_path = os.path.join(
            PROJECT_ROOT,
            'data',
            'raw',
            'raw_beneficiary_data.csv'
        )

    if courses_path is None:

        courses_path = os.path.join(
            PROJECT_ROOT,
            'data',
            'reference',
            'courses.csv'
        )

    np.random.seed(seed)
    random.seed(seed)

    # ==========================================================
    # LOAD DATA
    # ==========================================================

    print("Loading reference data...")

    df_b = pd.read_csv(
        beneficiaries_path
    )

    df_b = df_b.drop_duplicates(
        subset=['beneficiary_id']
    )

    df_c = pd.read_csv(
        courses_path
    )

    # ==========================================================
    # CLEAN TEXT
    # ==========================================================

    df_b['clean_career'] = (
        df_b['career_interest']
        .apply(clean_str)
    )

    df_c['clean_sector'] = (
        df_c['sector']
        .apply(clean_str)
    )

    # ==========================================================
    # EDUCATION ORDER
    # ==========================================================

    edu_ord = {
        'no_formal': 0,
        'primary': 1,
        'middle': 2,
        'secondary': 3,
        'senior_secondary': 4,
        'graduate': 5,
        'post_graduate': 6
    }

    df_b['edu_score'] = (
        df_b['education_level']
        .apply(
            lambda x:
            edu_ord.get(
                clean_str(x),
                0
            )
        )
    )

    df_c['req_edu_score'] = (
        df_c['minimum_education']
        .apply(
            lambda x:
            edu_ord.get(
                clean_str(x),
                0
            )
        )
    )

    # ==========================================================
    # SAMPLE BENEFICIARIES
    # ==========================================================

    ben_ids = (
        df_b['beneficiary_id']
        .dropna()
        .unique()
    )

    sample_size = min(
        4000,
        len(ben_ids)
    )

    sampled_bens = np.random.choice(
        ben_ids,
        size=sample_size,
        replace=False
    )

    # ==========================================================
    # DICTIONARIES
    # ==========================================================

    b_dict = (
        df_b
        .set_index('beneficiary_id')
        .to_dict('index')
    )

    c_dict = (
        df_c
        .set_index('course_id')
        .to_dict('index')
    )

    course_ids = (
        df_c['course_id']
        .tolist()
    )

    interactions = []

    # ==========================================================
    # GENERATE INTERACTIONS
    # ==========================================================

    print(
        "Generating interactions "
        "(this may take a moment)..."
    )

    for i in range(n_interactions):

        if i % 5000 == 0:

            print(
                f"Generated {i} / "
                f"{n_interactions}"
            )

        # ------------------------------------------------------
        # Random beneficiary + course
        # ------------------------------------------------------

        b_id = random.choice(
            sampled_bens
        )

        c_id = random.choice(
            course_ids
        )

        b = b_dict[b_id]
        c = c_dict[c_id]

        # ======================================================
        # START COMPATIBILITY SCORE
        # ======================================================

        score = -1.2

        # ======================================================
        # 1. CAREER INTEREST MATCH
        # ======================================================

        career_match = text_match(
            b.get('career_interest', ''),
            c.get('sector', '')
        )

        if career_match:

            score += 3.0

        # ======================================================
        # 2. PREFERRED INDUSTRY MATCH
        # ======================================================

        industry_match = text_match(
            b.get('preferred_industry', ''),
            c.get('industry', c.get('sector', ''))
        )

        if industry_match:

            score += 2.0

        # ======================================================
        # 3. PREFERRED OCCUPATION MATCH
        # ======================================================

        occupation = normalize_text(
            b.get('preferred_occupation', '')
        )

        job_role = normalize_text(
            c.get('job_role', '')
        )

        course_name = normalize_text(
            c.get('course_name', '')
        )

        occupation_match = False

        if occupation:

            if (
                occupation == job_role
                or occupation in job_role
                or occupation in course_name
            ):

                occupation_match = True

        if occupation_match:

            score += 3.0

        # ======================================================
        # 4. EDUCATION ELIGIBILITY
        # ======================================================

        b_edu = b.get(
            'edu_score',
            0
        )

        c_edu = c.get(
            'req_edu_score',
            0
        )

        if b_edu >= c_edu:

            score += 1.2

        else:

            score -= 2.5

        # ======================================================
        # 5. SKILL MATCH
        # ======================================================

        skill_match = calculate_skill_match(
            b,
            c
        )

        score += (
            skill_match * 2.0
        )

        # ======================================================
        # 6. REQUIRED SKILL LEVEL
        # ======================================================

        existing_skill = normalize_text(
            b.get(
                'existing_skill_level',
                'Beginner'
            )
        )

        required_skill = normalize_text(
            c.get(
                'required_skill_level',
                'Beginner'
            )
        )

        skill_level_map = {
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3
        }

        b_skill_level = skill_level_map.get(
            existing_skill,
            1
        )

        c_skill_level = skill_level_map.get(
            required_skill,
            1
        )

        if b_skill_level >= c_skill_level:

            score += 0.8

        elif b_skill_level + 1 >= c_skill_level:

            score += 0.2

        else:

            score -= 0.8

        # ======================================================
        # 7. LANGUAGE MATCH
        # ======================================================

        preferred_language = normalize_text(
            b.get(
                'preferred_language',
                ''
            )
        )

        course_languages = normalize_text(
            c.get(
                'language',
                ''
            )
        )

        if (
            preferred_language
            and preferred_language in course_languages
        ):

            score += 1.0

        # ======================================================
        # 8. TRAINING MODE MATCH
        # ======================================================

        preferred_mode = normalize_text(
            b.get(
                'preferred_training_mode',
                ''
            )
        )

        course_mode = normalize_text(
            c.get(
                'delivery_mode',
                ''
            )
        )

        if (
            preferred_mode == course_mode
            or preferred_mode == 'blended'
            or course_mode == 'blended'
        ):

            score += 0.7

        # ======================================================
        # 9. LOCAL DEMAND
        # ======================================================

        demand_map = {
            'low': 0.25,
            'medium': 0.50,
            'high': 0.75,
            'very_high': 1.00
        }

        beneficiary_demand = demand_map.get(
            str(
                b.get(
                    'local_job_demand',
                    'Medium'
                )
            ).lower().strip(),
            0.5
        )

        course_demand = demand_map.get(
            str(
                c.get(
                    'local_demand',
                    'Medium'
                )
            ).lower().strip(),
            0.5
        )

        demand_score = (
            beneficiary_demand
            * course_demand
        )

        score += (
            demand_score * 1.2
        )

        # ======================================================
        # 10. DISTANCE
        # ======================================================

        try:

            distance = float(
                b.get(
                    'distance_to_training_center_km',
                    50
                )
            )

        except (
            TypeError,
            ValueError
        ):

            distance = 50

        if pd.isna(distance):

            distance = 50

        if (
            course_mode == 'online'
            or distance <= 10
        ):

            score += 0.6

        elif distance <= 25:

            score += 0.3

        elif distance <= 50:

            score += 0.0

        else:

            score -= 0.4

        # ======================================================
        # 11. AGE ELIGIBILITY
        # ======================================================

        try:

            age = float(
                b.get(
                    'age',
                    25
                )
            )

        except (
            TypeError,
            ValueError
        ):

            age = 25

        if pd.isna(age):

            age = 25

        try:

            age_min = float(
                c.get(
                    'age_min',
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            age_min = 0

        try:

            age_max = float(
                c.get(
                    'age_max',
                    100
                )
            )

        except (
            TypeError,
            ValueError
        ):

            age_max = 100

        if (
            age_min <= age <= age_max
        ):

            score += 0.8

        else:

            score -= 2.0

        # ======================================================
        # 12. LOCAL INDUSTRY
        # ======================================================

        local_industry = normalize_text(
            b.get(
                'local_industry',
                ''
            )
        )

        course_industry = normalize_text(
            c.get(
                'industry',
                c.get(
                    'sector',
                    ''
                )
            )
        )

        if (
            local_industry
            and course_industry
            and (
                local_industry in course_industry
                or course_industry in local_industry
            )
        ):

            score += 0.8

        # ======================================================
        # ADD SMALL RANDOM NOISE
        # ======================================================
        #
        # This prevents the synthetic dataset from becoming
        # unrealistically perfect.
        #
        # Real recommendation systems contain uncertainty.
        #

        score += np.random.normal(
            0,
            0.6
        )

        # ======================================================
        # CONVERT SCORE → PROBABILITY
        # ======================================================

        prob_enroll = 1.0 / (
            1.0
            + np.exp(
                -np.clip(
                    score,
                    -8,
                    8
                )
            )
        )

        # ------------------------------------------------------
        # Enrollment
        # ------------------------------------------------------

        enrolled = (
            1
            if random.random() < prob_enroll
            else 0
        )

        completed = 0
        comp_score = np.nan
        emp_after = 0
        emp_months = np.nan
        sat_score = np.nan
        outcome = 0

        # ======================================================
        # ENROLLED
        # ======================================================

        if enrolled:

            # --------------------------------------------------
            # Completion probability
            # --------------------------------------------------

            prob_comp = 0.55

            if b_edu >= c_edu:

                prob_comp += 0.10

            else:

                prob_comp -= 0.15

            prob_comp += (
                skill_match * 0.20
            )

            if occupation_match:

                prob_comp += 0.08

            prob_comp = np.clip(
                prob_comp,
                0.10,
                0.95
            )

            completed = (
                1
                if random.random()
                < prob_comp
                else 0
            )

            # ==================================================
            # COMPLETED
            # ==================================================

            if completed:

                # --------------------------------------------------
                # Completion score
                # --------------------------------------------------

                base_completion = (
                    55
                    + skill_match * 30
                )

                if career_match:

                    base_completion += 5

                if occupation_match:

                    base_completion += 5

                comp_score = round(
                    np.clip(
                        np.random.normal(
                            base_completion,
                            8
                        ),
                        50,
                        100
                    ),
                    1
                )

                # --------------------------------------------------
                # Employment probability
                # --------------------------------------------------

                demand_text = str(
                    c.get(
                        'local_demand',
                        'Medium'
                    )
                ).lower().strip()

                demand_prob = {
                    'low': 0.30,
                    'medium': 0.50,
                    'high': 0.70,
                    'very_high': 0.82
                }.get(
                    demand_text,
                    0.50
                )

                prob_emp = demand_prob

                # Strong relevance improves employment
                if career_match:

                    prob_emp += 0.08

                if industry_match:

                    prob_emp += 0.06

                if occupation_match:

                    prob_emp += 0.08

                prob_emp += (
                    skill_match * 0.08
                )

                prob_emp = np.clip(
                    prob_emp,
                    0.05,
                    0.95
                )

                emp_after = (
                    1
                    if random.random()
                    < prob_emp
                    else 0
                )

                # --------------------------------------------------
                # Employment + satisfaction
                # --------------------------------------------------

                if emp_after:

                    emp_months = random.randint(
                        1,
                        36
                    )

                    satisfaction_base = 3.5

                    if career_match:
                        satisfaction_base += 0.3

                    if occupation_match:
                        satisfaction_base += 0.4

                    if industry_match:
                        satisfaction_base += 0.2

                    sat_score = round(
                        np.clip(
                            np.random.normal(
                                satisfaction_base,
                                0.4
                            ),
                            3.0,
                            5.0
                        ),
                        1
                    )

                else:

                    sat_score = round(
                        np.clip(
                            np.random.normal(
                                3.0,
                                0.6
                            ),
                            2.0,
                            4.5
                        ),
                        1
                    )

                # --------------------------------------------------
                # Final positive outcome
                # --------------------------------------------------

                if (
                    emp_after == 1
                    or sat_score >= 3.5
                ):

                    outcome = 1

            # ==================================================
            # NOT COMPLETED
            # ==================================================

            else:

                sat_score = round(
                    np.clip(
                        np.random.normal(
                            2.0,
                            0.6
                        ),
                        1.0,
                        3.0
                    ),
                    1
                )

                emp_after = (
                    1
                    if random.random() < 0.10
                    else 0
                )

                if emp_after:

                    emp_months = random.randint(
                        1,
                        12
                    )

        # ======================================================
        # SAVE INTERACTION
        # ======================================================

        interactions.append({
            'interaction_id':
                f"INT_{100000 + i}",

            'beneficiary_id':
                b_id,

            'course_id':
                c_id,

            'enrolled':
                enrolled,

            'completed':
                completed,

            'completion_score':
                comp_score,

            'employment_after_training':
                emp_after,

            'employment_months':
                emp_months,

            'satisfaction_score':
                sat_score,

            'outcome':
                outcome
        })

    # ==========================================================
    # CREATE DATAFRAME
    # ==========================================================

    df_int = pd.DataFrame(
        interactions
    )

    # ==========================================================
    # SAVE
    # ==========================================================

    save_path = os.path.join(
        PROJECT_ROOT,
        'data',
        'raw',
        'historical_interactions.csv'
    )

    os.makedirs(
        os.path.dirname(save_path),
        exist_ok=True
    )

    df_int.to_csv(
        save_path,
        index=False
    )

    print(
        f"Generated {len(df_int)} "
        f"synthetic interactions and saved to "
        f"{save_path}"
    )

    # ==========================================================
    # BASIC SUMMARY
    # ==========================================================

    print("\nInteraction summary:")

    print(
        f"Enrollment rate: "
        f"{df_int['enrolled'].mean():.3f}"
    )

    print(
        f"Completion rate among enrolled: "
        f"{df_int.loc[df_int['enrolled'] == 1, 'completed'].mean():.3f}"
    )

    print(
        f"Positive outcome rate: "
        f"{df_int['outcome'].mean():.3f}"
    )


if __name__ == '__main__':

    b_path = os.path.join(
        PROJECT_ROOT,
        'data',
        'raw',
        'raw_beneficiary_data.csv'
    )

    c_path = os.path.join(
        PROJECT_ROOT,
        'data',
        'reference',
        'courses.csv'
    )

    if (
        os.path.exists(b_path)
        and os.path.exists(c_path)
    ):

        generate_interactions(
            b_path,
            c_path
        )

    else:

        print(
            "Please generate courses "
            "and beneficiaries first."
        )