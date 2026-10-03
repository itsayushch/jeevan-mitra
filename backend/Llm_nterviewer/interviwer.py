import json
import requests
from pathlib import Path
import ollama

try:
    from mapper import map_llm_profile
except ImportError:
    from Llm_nterviewer.mapper import map_llm_profile


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

USER_PROFILE_FILE = BASE_DIR / "user_profile.json"
ML_PROFILE_FILE = BASE_DIR / "ml_profile.json"

API_URL = "http://127.0.0.1:8000/predict"


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an AI interviewer for a government livelihood and skill
recommendation system.

Your job is ONLY to conduct the interview and extract useful
beneficiary information.

DO NOT recommend courses, jobs, occupations, or training during
the interview.

The recommendation will be handled later by a separate ML model.

------------------------------------------------------------
INTERVIEW RULES
------------------------------------------------------------

1. Ask only ONE question at a time.

2. Keep the conversation natural and friendly.

3. Ask broad and useful questions instead of asking many tiny
   questions separately.

4. The user may provide multiple pieces of information in one
   answer.

   Example:
   User:
   "I am 20 years old, completed 12th and I live in Malda.
   I am unemployed and interested in IT."

   You should extract ALL of those facts.

5. NEVER ask again for information that the user has already
   provided.

6. Adapt the next question based on the information already
   collected.

7. If the user gives more information than expected, extract
   everything useful from it.

8. If important information is missing, ask about it naturally.

9. Do not ask unnecessary questions.

10. Finish the interview when enough important information has
    been collected for the recommendation system.

11. Do NOT force the user to answer every possible field.

12. If something is unknown, use null.

13. NEVER invent information.

14. Never assume:
    - location
    - education
    - income
    - skills
    - experience
    - occupation
    - language
    - preferences
    - training history

15. Do not directly ask for backend-derived information such as:
    - latitude
    - longitude
    - distance to training center
    - local job demand
    - local industry
    - training center availability

    These can be obtained later from backend/database systems.

------------------------------------------------------------
IMPORTANT INTERVIEW FIELDS
------------------------------------------------------------

Collect information when naturally available:

- age
- gender
- state
- district
- rural_urban
- education_level
- education_stream
- annual_family_income
- employment_status
- current_occupation
- work_experience_years
- digital_literacy
- communication_skill
- numerical_skill
- technical_skill
- entrepreneurial_skill
- existing_skill_level
- career_interest
- preferred_occupation
- preferred_industry
- preferred_work_type
- preferred_training_mode
- preferred_language
- previous_training
- previous_training_count
- preferred_duration

------------------------------------------------------------
QUESTION STRATEGY
------------------------------------------------------------

Start naturally.

Good examples:

"Could you tell me a little about yourself, such as your age,
education, and where you are from?"

"Could you tell me about the skills you currently have or feel
comfortable using?"

"What kind of work or career are you interested in?"

"Is there a particular type of work environment or training
format you prefer?"

Do not ask all of these separately if the user already provides
the information.

If the user says:

"I completed 12th and I am from Malda."

Do not ask again:

"What is your education?"

Instead ask about another missing important area.

------------------------------------------------------------
OUTPUT FORMAT
------------------------------------------------------------

Return ONLY valid JSON.

The JSON must have exactly these top-level fields:

{
    "message": "The next message/question for the user",
    "profile": {
        "age": null,
        "gender": null,
        "state": null,
        "district": null,
        "rural_urban": null,
        "education_level": null,
        "education_stream": null,
        "annual_family_income": null,
        "employment_status": null,
        "current_occupation": null,
        "work_experience_years": null,
        "digital_literacy": null,
        "communication_skill": null,
        "numerical_skill": null,
        "technical_skill": null,
        "entrepreneurial_skill": null,
        "existing_skill_level": null,
        "career_interest": null,
        "preferred_occupation": null,
        "preferred_industry": null,
        "preferred_work_type": null,
        "preferred_training_mode": null,
        "preferred_language": null,
        "previous_training": null,
        "previous_training_count": null,
        "preferred_duration": null
    },
    "interview_complete": false
}

------------------------------------------------------------
PROFILE RULES
------------------------------------------------------------

The profile should contain the information extracted from the
entire conversation so far.

Preserve previously collected information.

Do not erase known information unless the user corrects it.

If the user corrects something, update it.

If information is unavailable, keep it null.

------------------------------------------------------------
COMPLETION
------------------------------------------------------------

Set:

"interview_complete": true

when enough useful information has been collected for the
recommendation system.

Do not keep asking questions just to fill every field.

When interview_complete is true, message should briefly tell
the user that the interview is complete.

Do not provide recommendations.
"""


# ============================================================
# INITIAL CONVERSATION
# ============================================================

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    },
    {
        "role": "user",
        "content": """
Start the interview.

Introduce yourself briefly and ask the first useful question.

Do not ask multiple questions at once.
"""
    }
]


# ============================================================
# HELPER: SAVE JSON
# ============================================================

def save_json(file_path: Path, data: dict):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# SEND PROFILE TO FASTAPI
# ============================================================

def send_to_api(ml_profile: dict):

    print("\n" + "=" * 60)
    print("SENDING PROFILE TO ML API")
    print("=" * 60)

    try:

        response = requests.post(
            API_URL,
            json=ml_profile,
            timeout=60
        )

        response.raise_for_status()

        result = response.json()

        print("\nML API RESPONSE:")
        print(json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        ))

        return result

    except requests.exceptions.ConnectionError:

        print("\nERROR: Could not connect to FastAPI.")

        print("\nMake sure you have started the API with:")

        print("uvicorn api.main:app --reload")

        return None

    except requests.exceptions.Timeout:

        print("\nERROR: FastAPI request timed out.")

        return None

    except requests.exceptions.HTTPError as e:

        print("\nERROR: FastAPI returned an HTTP error.")

        print(e)

        try:
            print(response.text)
        except Exception:
            pass

        return None

    except Exception as e:

        print("\nERROR while sending profile to API:")
        print(e)

        return None


# ============================================================
# PRINT RECOMMENDATIONS
# ============================================================

def print_recommendations(result):

    if not result:
        return

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    recommendations = result.get("recommendations", [])

    if not recommendations:

        print("\nNo recommendations returned.")

        return

    for index, recommendation in enumerate(
        recommendations,
        start=1
    ):

        print(f"\nRecommendation {index}")

        if isinstance(recommendation, dict):

            for key, value in recommendation.items():

                print(f"{key}: {value}")

        else:

            print(recommendation)


# ============================================================
# MAIN INTERVIEW
# ============================================================

def main():

    print("=" * 60)
    print("JEEVANMITRA AI INTERVIEW")
    print("=" * 60)

    print("\nStarting Qwen3 interview...")
    print("Type your answers below.")
    print("Type 'exit' if you want to stop.\n")

    while True:

        try:

            # ------------------------------------------------
            # CALL LOCAL QWEN MODEL
            # ------------------------------------------------

            response = ollama.chat(
                model="qwen3:8b",
                messages=messages,
                format="json"
            )

            # ------------------------------------------------
            # GET MODEL RESPONSE
            # ------------------------------------------------

            content = response["message"]["content"]

            # ------------------------------------------------
            # CONVERT JSON STRING -> PYTHON DICT
            # ------------------------------------------------

            result = json.loads(content)

            # ------------------------------------------------
            # DISPLAY AI MESSAGE
            # ------------------------------------------------

            print("\nAI:")
            print(result.get("message", ""))

            # ------------------------------------------------
            # ADD AI RESPONSE TO CONVERSATION HISTORY
            # ------------------------------------------------

            messages.append(
                {
                    "role": "assistant",
                    "content": content
                }
            )

            # ------------------------------------------------
            # CHECK INTERVIEW COMPLETION
            # ------------------------------------------------

            if result.get("interview_complete", False):

                print("\n" + "=" * 60)
                print("INTERVIEW COMPLETE")
                print("=" * 60)

                profile = result.get("profile", {})

                # ============================================
                # SAVE RAW USER PROFILE
                # ============================================

                save_json(
                    USER_PROFILE_FILE,
                    profile
                )

                print(
                    f"\nRaw profile saved to:\n"
                    f"{USER_PROFILE_FILE}"
                )

                # ============================================
                # MAP PROFILE FOR ML
                # ============================================

                print("\nMapping profile for ML...")

                try:

                    ml_profile = map_llm_profile(
                        profile
                    )

                except Exception as e:

                    print(
                        "\nERROR while mapping profile:"
                    )

                    print(e)

                    return

                # ============================================
                # SAVE ML PROFILE
                # ============================================

                save_json(
                    ML_PROFILE_FILE,
                    ml_profile
                )

                print(
                    f"\nML profile saved to:\n"
                    f"{ML_PROFILE_FILE}"
                )

                # ============================================
                # SHOW ML PROFILE
                # ============================================

                print("\nML PROFILE:")

                print(
                    json.dumps(
                        ml_profile,
                        indent=4,
                        ensure_ascii=False
                    )
                )

                # ============================================
                # SEND TO FASTAPI
                # ============================================

                api_result = send_to_api(
                    ml_profile
                )

                # ============================================
                # PRINT RECOMMENDATIONS
                # ============================================

                print_recommendations(
                    api_result
                )

                print("\n" + "=" * 60)
                print("PIPELINE FINISHED")
                print("=" * 60)

                return

            # ------------------------------------------------
            # GET USER ANSWER
            # ------------------------------------------------

            user_answer = input("\nYou: ").strip()

            if user_answer.lower() in {
                "exit",
                "quit",
                "stop"
            }:

                print("\nInterview stopped.")

                return

            if not user_answer:

                print(
                    "\nPlease provide an answer."
                )

                continue

            # ------------------------------------------------
            # ADD USER ANSWER TO CONVERSATION
            # ------------------------------------------------

            messages.append(
                {
                    "role": "user",
                    "content": user_answer
                }
            )

        except KeyboardInterrupt:

            print(
                "\n\nInterview stopped by user."
            )

            return

        except json.JSONDecodeError:

            print(
                "\nERROR: Qwen returned invalid JSON."
            )

            print(
                "\nRaw response:"
            )

            print(
                response["message"]["content"]
            )

            return

        except Exception as e:

            print(
                "\nERROR:"
            )

            print(e)

            return


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()