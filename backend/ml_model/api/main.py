import os
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ============================================================
# PROJECT PATH
# ============================================================

# D:\sih
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Allow Python to import from D:\sih\src
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORT EXISTING ML PREDICTION FUNCTION
# ============================================================

from src.prediction.predict import predict


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="JeevanMitra 2.0 - PM-AJAY Recommendation API",
    description="AI-based NSQF skill training recommendation API",
    version="1.0.0"
)


# ============================================================
# REQUEST SCHEMA
# ============================================================

class BeneficiaryRequest(BaseModel):

    beneficiary_id: str = "API_USER"

    age: Optional[float] = None
    gender: Optional[str] = None

    state: Optional[str] = None
    district: Optional[str] = None
    rural_urban: Optional[str] = None
    social_category: Optional[str] = None

    education_level: Optional[str] = None
    education_stream: Optional[str] = None

    annual_family_income: Optional[float] = None

    employment_status: Optional[str] = None
    current_occupation: Optional[str] = None
    work_experience_years: Optional[float] = None

    digital_literacy: Optional[float] = None
    communication_skill: Optional[float] = None
    numerical_skill: Optional[float] = None
    technical_skill: Optional[float] = None
    entrepreneurial_skill: Optional[float] = None

    existing_skill_level: Optional[str] = None

    career_interest: Optional[str] = None
    preferred_occupation: Optional[str] = None
    preferred_industry: Optional[str] = None

    preferred_work_type: Optional[str] = None
    preferred_training_mode: Optional[str] = None
    preferred_language: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    distance_to_training_center_km: Optional[float] = None
    training_center_availability: Optional[str] = None

    local_job_demand: Optional[str] = None
    local_industry: Optional[str] = None

    previous_training: Optional[str] = None
    previous_training_count: Optional[int] = None
    training_completion_rate: Optional[float] = None

    preferred_duration: Optional[str] = None

    # Number of recommendations requested
    top_k: int = Field(default=3, ge=1, le=10)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "JeevanMitra 2.0 Recommendation API is running",
        "status": "online",
        "model_endpoint": "/predict",
        "documentation": "/docs"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# ML PREDICTION ENDPOINT
# ============================================================

@app.post("/predict")
def predict_courses(request: BeneficiaryRequest):

    try:

        # Convert request object to dictionary
        beneficiary_profile = request.model_dump()

        # Extract top_k
        top_k = beneficiary_profile.pop("top_k")

        # Remove fields that were not provided by the user
        # Your existing predict() function supplies defaults
        # for missing fields.
        beneficiary_profile = {
            key: value
            for key, value in beneficiary_profile.items()
            if value is not None
        }

        # ====================================================
        # CALL YOUR EXISTING ML PIPELINE
        # ====================================================

        result = predict(
            beneficiary_profile=beneficiary_profile,
            top_k=top_k,
            use_fallback=False
        )

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


# ============================================================
# FALLBACK PREDICTION ENDPOINT
# ============================================================

@app.post("/predict/fallback")
def predict_fallback(request: BeneficiaryRequest):

    try:

        beneficiary_profile = request.model_dump()

        top_k = beneficiary_profile.pop("top_k")

        beneficiary_profile = {
            key: value
            for key, value in beneficiary_profile.items()
            if value is not None
        }

        # Use your existing content-based fallback
        result = predict(
            beneficiary_profile=beneficiary_profile,
            top_k=top_k,
            use_fallback=True
        )

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Fallback prediction failed: {str(e)}"
        )


# ============================================================
# RUN DIRECTLY WITH:
#
# python api/main.py
#
# OR PREFERRED:
#
# uvicorn api.main:app --reload
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

