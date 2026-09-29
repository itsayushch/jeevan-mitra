import os
import pandas as pd
import numpy as np
import random


# ==========================================
# SYNTHETIC DATA GENERATION SCRIPT
# ALL DATA GENERATED IS STRICTLY SYNTHETIC
# ==========================================


def generate_courses(n_courses=200, seed=42):

    np.random.seed(seed)
    random.seed(seed)

    # ==========================================================
    # SECTORS
    # ==========================================================

    sectors = [
        'IT / ITES',
        'Healthcare',
        'Retail',
        'Agriculture',
        'Construction',
        'Automotive',
        'Electronics',
        'Tourism',
        'Hospitality',
        'Banking / Finance',
        'Beauty & Wellness',
        'Logistics',
        'Manufacturing',
        'Green Jobs',
        'Telecom',
        'Entrepreneurship'
    ]

    sector_weights = [
        0.12,
        0.12,
        0.08,
        0.08,
        0.08,
        0.05,
        0.05,
        0.04,
        0.05,
        0.05,
        0.05,
        0.05,
        0.05,
        0.05,
        0.04,
        0.08
    ]

    sector_weights = [
        w / sum(sector_weights)
        for w in sector_weights
    ]

    # ==========================================================
    # COMMON VALUES
    # ==========================================================

    education_levels = [
        'No_Formal',
        'Primary',
        'Middle',
        'Secondary',
        'Senior_Secondary',
        'Graduate',
        'Post_Graduate'
    ]

    skill_levels = [
        'Beginner',
        'Intermediate',
        'Advanced'
    ]

    delivery_modes = [
        'Online',
        'Offline',
        'Blended'
    ]

    languages_pool = [
        'Hindi',
        'English',
        'Bengali',
        'Tamil',
        'Telugu',
        'Marathi',
        'Gujarati',
        'Kannada',
        'Odia',
        'Malayalam'
    ]

    states = [
        'Uttar Pradesh',
        'Bihar',
        'Maharashtra',
        'Madhya Pradesh',
        'Rajasthan',
        'West Bengal',
        'Karnataka',
        'Tamil Nadu',
        'Gujarat'
    ]

    courses_data = []

    # ==========================================================
    # COURSE COUNT
    # ==========================================================

    sector_counts = np.random.multinomial(
        n_courses,
        sector_weights
    )

    course_id_counter = 1000

    # ==========================================================
    # GENERATE COURSES
    # ==========================================================

    for i, sector in enumerate(sectors):

        count = sector_counts[i]

        sector_prefix = str(i + 1)

        for _ in range(count):

            course_id = (
                f"NSQ_{sector_prefix}"
                f"{course_id_counter:03d}"
            )

            course_id_counter += 1

            # --------------------------------------------------
            # Course name
            # --------------------------------------------------

            course_name = (
                f"{sector} Technician "
                f"{random.randint(1, 100)}"
            )

            if sector == 'IT / ITES':

                course_name = random.choice([
                    'Domestic Data Entry Operator',
                    'Web Developer',
                    'Cybersecurity Basics',
                    'Cloud Computing Basics'
                ])

            elif sector == 'Healthcare':

                course_name = random.choice([
                    'General Duty Assistant',
                    'Home Health Aide',
                    'Phlebotomy Technician',
                    'Pharmacy Assistant'
                ])

            elif sector == 'Agriculture':

                course_name = random.choice([
                    'Organic Farming',
                    'Precision Agriculture',
                    'Drone Operator',
                    'Soil Tester'
                ])

            elif sector == 'Construction':

                course_name = random.choice([
                    'Masonry',
                    'Plumbing Basics',
                    'Electrician',
                    'Welding Technician'
                ])

            elif sector == 'Entrepreneurship':

                course_name = random.choice([
                    'Micro-Enterprise Business Development',
                    'Agri-Business & Rural Startup',
                    'Small Business Management',
                    'E-Commerce & Digital Store Setup',
                    'Self-Employment Entrepreneurship'
                ])

            # --------------------------------------------------
            # NSQF
            # --------------------------------------------------

            nsqf = random.choices(
                [
                    1, 2, 3, 4, 5,
                    6, 7, 8, 9, 10
                ],
                weights=[
                    0.05,
                    0.10,
                    0.20,
                    0.30,
                    0.20,
                    0.10,
                    0.05,
                    0.00,
                    0.00,
                    0.00
                ]
            )[0]

            # --------------------------------------------------
            # Sub-sector
            # --------------------------------------------------

            sub_sector = (
                f"{sector} Sub-Sector "
                f"{random.randint(1, 5)}"
            )

            # --------------------------------------------------
            # Duration
            # --------------------------------------------------

            duration = (
                random.randint(40, 200)
                * max(1, nsqf // 2)
            )

            if duration > 1200:
                duration = 1200

            # --------------------------------------------------
            # Minimum education
            # --------------------------------------------------

            edu_idx = min(
                len(education_levels) - 1,
                max(
                    0,
                    nsqf - 3
                    + random.randint(-1, 1)
                )
            )

            min_edu = education_levels[
                edu_idx
            ]

            # --------------------------------------------------
            # Required skill
            # --------------------------------------------------

            if nsqf > 6:

                req_skill = 'Advanced'

            elif nsqf > 4:

                req_skill = 'Intermediate'

            else:

                req_skill = 'Beginner'

            # --------------------------------------------------
            # Delivery mode
            # --------------------------------------------------

            del_mode = random.choice(
                delivery_modes
            )

            # --------------------------------------------------
            # Languages
            # --------------------------------------------------

            langs = random.sample(
                languages_pool,
                k=random.randint(1, 3)
            )

            if (
                'Hindi' not in langs
                and 'English' not in langs
            ):

                langs.append(
                    random.choice([
                        'Hindi',
                        'English'
                    ])
                )

            language = ", ".join(langs)

            # --------------------------------------------------
            # Age range
            # --------------------------------------------------

            age_min = random.randint(
                14,
                21
            )

            age_max = random.randint(
                35,
                60
            )

            # --------------------------------------------------
            # Meaningful job role
            # --------------------------------------------------

            if sector == 'IT / ITES':

                job_role = random.choice([
                    'Web Developer',
                    'Data Entry Operator',
                    'Cybersecurity Specialist',
                    'Cloud Computing Specialist'
                ])

            elif sector == 'Healthcare':

                job_role = random.choice([
                    'Healthcare Assistant',
                    'Home Health Aide',
                    'Phlebotomy Technician',
                    'Pharmacy Assistant'
                ])

            elif sector == 'Agriculture':

                job_role = random.choice([
                    'Agriculture Worker',
                    'Organic Farming Technician',
                    'Precision Agriculture Technician',
                    'Drone Operator'
                ])

            elif sector == 'Construction':

                job_role = random.choice([
                    'Mason',
                    'Plumber',
                    'Electrician',
                    'Welding Technician'
                ])

            elif sector == 'Entrepreneurship':

                job_role = random.choice([
                    'Micro-Enterprise Owner',
                    'Agri-Business Founder',
                    'Small Business Manager',
                    'Digital Store Entrepreneur'
                ])

            else:

                job_role = (
                    f"{sector} Specialist"
                )

            # --------------------------------------------------
            # Industry
            # --------------------------------------------------

            industry = sector

            # --------------------------------------------------
            # Salary
            # --------------------------------------------------

            base_sal = (
                8000
                + (nsqf * 5000)
            )

            avg_salary = int(
                base_sal
                * random.uniform(
                    0.8,
                    1.2
                )
            )

            if avg_salary > 80000:
                avg_salary = 80000

            # --------------------------------------------------
            # Local demand
            # --------------------------------------------------

            local_demand = random.choice([
                'Low',
                'Medium',
                'High',
                'Very_High'
            ])

            # --------------------------------------------------
            # Location
            # --------------------------------------------------

            course_location = random.choice(
                states
            )

            # --------------------------------------------------
            # Add course
            # --------------------------------------------------

            courses_data.append({
                'course_id': course_id,
                'course_name': course_name,
                'nsqf_level': nsqf,
                'sector': sector,
                'sub_sector': sub_sector,
                'course_duration_hours': duration,
                'minimum_education': min_edu,
                'required_skill_level': req_skill,
                'delivery_mode': del_mode,
                'language': language,
                'age_min': age_min,
                'age_max': age_max,
                'job_role': job_role,
                'industry': industry,
                'average_salary': avg_salary,
                'local_demand': local_demand,
                'course_location': course_location
            })

    # ==========================================================
    # CREATE DATAFRAME
    # ==========================================================

    df = pd.DataFrame(
        courses_data
    )

    if len(df) > n_courses:

        df = df.iloc[
            :n_courses
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

    save_path = os.path.join(
        PROJECT_ROOT,
        'data',
        'reference',
        'courses.csv'
    )

    os.makedirs(
        os.path.dirname(save_path),
        exist_ok=True
    )

    df.to_csv(
        save_path,
        index=False
    )

    print(
        f"Generated {len(df)} synthetic courses "
        f"and saved to {save_path}"
    )


if __name__ == '__main__':
    generate_courses()