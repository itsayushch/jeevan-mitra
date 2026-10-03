import json
from pathlib import Path


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "user_profile.json"
OUTPUT_FILE = BASE_DIR / "ml_profile.json"


# ============================================================
# MAPPING TABLES
# ============================================================

SKILL_LEVEL_MAP = {
    "very low": 1,
    "low": 2,
    "basic": 3,
    "beginner": 3,
    "below average": 4,
    "moderate": 5,
    "average": 5,
    "intermediate": 6,
    "good": 7,
    "advanced": 8,
    "very good": 9,
    "expert": 10,
}


EDUCATION_MAP = {
    "10th": "Secondary",
    "class 10": "Secondary",
    "secondary": "Secondary",
    "matric": "Secondary",
    "ssc": "Secondary",

    "12th": "Senior_Secondary",
    "class 12": "Senior_Secondary",
    "senior secondary": "Senior_Secondary",
    "intermediate": "Senior_Secondary",
    "hsc": "Senior_Secondary",
    "+2": "Senior_Secondary",
    "puc": "Senior_Secondary",

    "diploma": "Diploma",

    "graduate": "Graduate",
    "graduation": "Graduate",
    "bachelor": "Graduate",
    "bachelors": "Graduate",

    "post graduate": "Post_Graduate",
    "postgraduate": "Post_Graduate",
    "master": "Post_Graduate",
    "masters": "Post_Graduate",
}


CAREER_MAP = {
    "it": "IT / ITES",
    "it industry": "IT / ITES",
    "it industries": "IT / ITES",
    "information technology": "IT / ITES",
    "information technologies": "IT / ITES",
    "software": "IT / ITES",
    "software development": "IT / ITES",
    "coding": "IT / ITES",
    "computer": "IT / ITES",
    "computers": "IT / ITES",
    "web development": "IT / ITES",
    "web developer": "IT / ITES",

    "health": "Healthcare",
    "healthcare": "Healthcare",
    "medical": "Healthcare",

    "farming": "Agriculture",
    "agriculture": "Agriculture",
    "agri": "Agriculture",

    "hospitality": "Hospitality",
    "hotel": "Hospitality",
    "hotels": "Hospitality",
}


EMPLOYMENT_MAP = {
    "employed": "Employed",
    "unemployed": "Unemployed",
    "student": "Student",
    "self employed": "Self_Employed",
    "self-employed": "Self_Employed",
    "looking for work": "Unemployed",
}


WORK_TYPE_MAP = {
    "full time": "Full_Time",
    "full-time": "Full_Time",
    "fulltime": "Full_Time",

    "part time": "Part_Time",
    "part-time": "Part_Time",
    "parttime": "Part_Time",

    "self employment": "Self_Employment",
    "self-employed": "Self_Employment",
    "self employed": "Self_Employment",

    "freelance": "Freelance",

    "remote": "Remote",

    "internship": "Internship",
}


TRAINING_MODE_MAP = {
    "online": "Online",
    "offline": "Offline",
    "in-person": "Offline",
    "in person": "Offline",
    "classroom": "Offline",
    "hybrid": "Hybrid",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_string(value):
    """
    Convert a value to a clean lowercase string.
    """
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        return value

    return str(value).strip()


def map_skill(value):
    """
    Convert qualitative skill levels to the numeric 1-10
    scale used by the ML dataset.
    """

    if value is None:
        return None

    # Already numeric
    if isinstance(value, (int, float)):
        if 1 <= value <= 10:
            return round(value)

        return None

    value = clean_string(value)

    if value is None:
        return None

    value_lower = value.lower()

    if value_lower in SKILL_LEVEL_MAP:
        return SKILL_LEVEL_MAP[value_lower]

    # Try numeric strings such as "5"
    try:
        number = float(value_lower)

        if 1 <= number <= 10:
            return round(number)

    except ValueError:
        pass

    return None


def map_education(value):
    if value is None:
        return None

    value = clean_string(value)

    if value is None:
        return None

    key = value.lower()

    return EDUCATION_MAP.get(key, value)


def map_career(value):
    if value is None:
        return None

    value = clean_string(value)

    if value is None:
        return None

    key = value.lower()

    return CAREER_MAP.get(key, value)


def map_employment(value):
    if value is None:
        return None

    value = clean_string(value)

    if value is None:
        return None

    key = value.lower()

    return EMPLOYMENT_MAP.get(key, value.title())


def map_work_type(value):
    """
    API/model expects a single string.

    If LLM returns:
        ["full time", "remote"]

    we use the first preference:
        "Full_Time"
    """

    if value is None:
        return None

    # If LLM gives a list
    if isinstance(value, list):

        if len(value) == 0:
            return None

        # Take first preference
        value = value[0]

    value = clean_string(value)

    if value is None:
        return None

    key = value.lower()

    return WORK_TYPE_MAP.get(key, value)


def map_training_mode(value):
    if value is None:
        return None

    value = clean_string(value)

    if value is None:
        return None

    key = value.lower()

    return TRAINING_MODE_MAP.get(key, value)


def map_language(value):
    """
    ML API expects one language string.

    If LLM returns:
        ["English", "Hindi"]

    use the first preference:
        "English"
    """

    if value is None:
        return None

    if isinstance(value, list):

        if len(value) == 0:
            return None

        value = value[0]

    value = clean_string(value)

    return value


def map_duration(value):
    """
    Convert duration into:

        Short
        Medium
        Long
    """

    if value is None:
        return None

    value = clean_string(value)

    if value is None:
        return None

    value_lower = value.lower()

    # Already normalized
    if value_lower == "short":
        return "Short"

    if value_lower == "medium":
        return "Medium"

    if value_lower == "long":
        return "Long"

    # Months
    if "month" in value_lower:

        try:
            number = float(
                value_lower.replace("months", "")
                .replace("month", "")
                .strip()
            )

            if number <= 2:
                return "Short"

            elif number <= 6:
                return "Medium"

            else:
                return "Long"

        except ValueError:
            pass

    # Weeks
    if "week" in value_lower:

        try:
            number = float(
                value_lower.replace("weeks", "")
                .replace("week", "")
                .strip()
            )

            if number <= 8:
                return "Short"

            elif number <= 24:
                return "Medium"

            else:
                return "Long"

        except ValueError:
            pass

    return value


# ============================================================
# MAIN MAPPER
# ============================================================

def map_llm_profile(llm_profile):
    """
    Convert the LLM-generated profile into the format expected
    by the existing ML recommendation system.
    """

    ml_profile = {}

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    if llm_profile.get("age") is not None:
        ml_profile["age"] = llm_profile["age"]

    if llm_profile.get("gender") is not None:
        ml_profile["gender"] = llm_profile["gender"]

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    if llm_profile.get("state") is not None:
        ml_profile["state"] = llm_profile["state"]

    if llm_profile.get("district") is not None:
        ml_profile["district"] = llm_profile["district"]

    if llm_profile.get("rural_urban") is not None:
        ml_profile["rural_urban"] = llm_profile["rural_urban"]

    # --------------------------------------------------------
    # EDUCATION
    # --------------------------------------------------------

    if llm_profile.get("education_level") is not None:
        ml_profile["education_level"] = map_education(
            llm_profile["education_level"]
        )

    if llm_profile.get("education_stream") is not None:
        ml_profile["education_stream"] = llm_profile[
            "education_stream"
        ]

    # --------------------------------------------------------
    # ECONOMIC INFORMATION
    # --------------------------------------------------------

    if llm_profile.get("annual_family_income") is not None:
        ml_profile["annual_family_income"] = (
            llm_profile["annual_family_income"]
        )

    # --------------------------------------------------------
    # EMPLOYMENT
    # --------------------------------------------------------

    if llm_profile.get("employment_status") is not None:
        ml_profile["employment_status"] = map_employment(
            llm_profile["employment_status"]
        )

    if llm_profile.get("current_occupation") is not None:
        ml_profile["current_occupation"] = (
            llm_profile["current_occupation"]
        )

    if llm_profile.get("work_experience_years") is not None:
        ml_profile["work_experience_years"] = (
            llm_profile["work_experience_years"]
        )

    # --------------------------------------------------------
    # SKILLS
    # --------------------------------------------------------

    skill_columns = [
        "digital_literacy",
        "communication_skill",
        "numerical_skill",
        "technical_skill",
        "entrepreneurial_skill",
    ]

    for column in skill_columns:

        if llm_profile.get(column) is not None:

            mapped_value = map_skill(
                llm_profile[column]
            )

            if mapped_value is not None:
                ml_profile[column] = mapped_value

    # --------------------------------------------------------
    # EXISTING SKILL LEVEL
    # --------------------------------------------------------

    if llm_profile.get("existing_skill_level") is not None:

        ml_profile["existing_skill_level"] = (
            llm_profile["existing_skill_level"]
        )

    # --------------------------------------------------------
    # CAREER
    # --------------------------------------------------------

    if llm_profile.get("career_interest") is not None:

        ml_profile["career_interest"] = map_career(
            llm_profile["career_interest"]
        )

    if llm_profile.get("preferred_occupation") is not None:

        ml_profile["preferred_occupation"] = (
            llm_profile["preferred_occupation"]
        )

    if llm_profile.get("preferred_industry") is not None:

        ml_profile["preferred_industry"] = (
            llm_profile["preferred_industry"]
        )

    # --------------------------------------------------------
    # WORK PREFERENCE
    # --------------------------------------------------------

    if llm_profile.get("preferred_work_type") is not None:

        ml_profile["preferred_work_type"] = map_work_type(
            llm_profile["preferred_work_type"]
        )

    # --------------------------------------------------------
    # TRAINING PREFERENCE
    # --------------------------------------------------------

    if llm_profile.get("preferred_training_mode") is not None:

        ml_profile["preferred_training_mode"] = (
            map_training_mode(
                llm_profile["preferred_training_mode"]
            )
        )

    if llm_profile.get("preferred_language") is not None:

        ml_profile["preferred_language"] = map_language(
            llm_profile["preferred_language"]
        )

    if llm_profile.get("preferred_duration") is not None:

        ml_profile["preferred_duration"] = map_duration(
            llm_profile["preferred_duration"]
        )

    # --------------------------------------------------------
    # PREVIOUS TRAINING
    # --------------------------------------------------------

    if llm_profile.get("previous_training") is not None:
        ml_profile["previous_training"] = (
            llm_profile["previous_training"]
        )

    if llm_profile.get("previous_training_count") is not None:
        ml_profile["previous_training_count"] = (
            llm_profile["previous_training_count"]
        )

    # --------------------------------------------------------
    # BACKEND-DERIVED FIELDS
    # --------------------------------------------------------
    # These normally should NOT come from the LLM.
    # They are copied only if they are already present.

    backend_fields = [
        "beneficiary_id",
        "social_category",
        "latitude",
        "longitude",
        "distance_to_training_center_km",
        "training_center_availability",
        "local_job_demand",
        "local_industry",
        "training_completion_rate",
    ]

    for field in backend_fields:

        if llm_profile.get(field) is not None:
            ml_profile[field] = llm_profile[field]

    return ml_profile


# ============================================================
# READ JSON → MAP → WRITE JSON
# ============================================================

def main():

    # Check input file
    if not INPUT_FILE.exists():

        print(f"ERROR: {INPUT_FILE} not found.")

        print(
            "\nRun interviwer.py first so that "
            "user_profile.json is created."
        )

        return

    # --------------------------------------------------------
    # READ user_profile.json
    # --------------------------------------------------------

    try:

        with open(
            INPUT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            llm_profile = json.load(file)

    except json.JSONDecodeError as e:

        print("ERROR: user_profile.json contains invalid JSON.")

        print(e)

        return

    # --------------------------------------------------------
    # MAP PROFILE
    # --------------------------------------------------------

    ml_profile = map_llm_profile(llm_profile)

    # --------------------------------------------------------
    # WRITE ml_profile.json
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            ml_profile,
            file,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------------

    print("\nLLM PROFILE:")
    print(json.dumps(
        llm_profile,
        indent=4,
        ensure_ascii=False
    ))

    print("\nML PROFILE:")
    print(json.dumps(
        ml_profile,
        indent=4,
        ensure_ascii=False
    ))

    print(
        f"\nML profile saved to:\n{OUTPUT_FILE}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()