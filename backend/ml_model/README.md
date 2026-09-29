# PM-AJAY / JeevanMitra 2.0 — NSQ Course Recommendation System

## 1. Overview
This project implements the PM-AJAY / JeevanMitra 2.0 NSQ Course Recommendation ML Pipeline. It matches beneficiaries with NSQF-aligned training courses using pointwise learning-to-rank, considering profile characteristics, course requirements, and historical interactions.

## 2. ⚠️ Disclaimer
All data used and generated in this repository is purely synthetic for demonstration purposes. It does not contain any real government or beneficiary data.

## 3. Architecture
```text
[Beneficiary Profile] 
       │
       ▼
[Eligibility Filter (Hard Constraints)]
       │
       ▼
[Feature Engineering (Profile-Course Pairs)]
       │
       ▼
[ML Scoring Pipeline (Pointwise LTR)]
       │
       ▼
[Ranking & Top-K Selection]
       │
       ▼
[Explanation Generation (Rule-based + SHAP)]
       │
       ▼
[Final Recommendations]
```

## 4. Dataset Structure
- **Beneficiaries**: `beneficiary_id`, demographic data, education, skills, preferences.
- **Courses**: `course_id`, NSQF level, sector, requirements, location.
- **Interactions**: Historical interactions indicating completion, dropout, enrollment.

## 5. Data Cleaning
- Handling missing values using domain-specific imputations (e.g., 'Unknown' for categorical, medians for continuous).
- Standardizing text fields and aligning to defined vocabularies.

## 6. EDA
Comprehensive exploratory data analysis reveals class imbalances in course popularities and geographical disparities, which inform the feature engineering steps.

## 7. Feature Engineering
- `career_interest_match`: 1 if beneficiary interest matches course sector.
- `education_eligibility`: Binary flag based on ordinal education comparison.
- `distance_penalty`: Computed using Haversine distance.
- `skill_match_score`: Difference between beneficiary skill and required skill.

## 8. Train/Test Split
GroupShuffleSplit is used grouped by `beneficiary_id` to ensure no data leakage across interactions from the same beneficiary, ensuring the model generalizes to new beneficiaries.

## 9. Scaling Strategy
See `reports/scaling_strategy.md` for a detailed breakdown of feature scaling techniques used.

## 10. Encoding Strategy
- Ordinal: Education, Skill level.
- One-Hot: State, Sector.
- Target Encoding: High cardinality fields like district if needed.

## 11. Data Leakage Prevention
Ensuring no future interaction data (e.g. completion rate) is aggregated into features used for training historical recommendations.

## 12. Model Selection
RandomForest, XGBoost, and LightGBM were evaluated. The best model is saved based on Precision@K and NDCG metrics.

## 13. Ranking Architecture
Filter -> Score -> Rank -> Explain. It filters ineligible courses first to drastically reduce inference time.

## 14. Evaluation Metrics
- **Classification**: AUC-ROC, F1-Score.
- **Ranking**: NDCG@5, Precision@5.

## 15. Prediction Process
Use `--step predict` to run inference. It expects a dictionary profile and returns top-K recommendations.

## 16. Explainability
Provides rule-based explanations for transparency and SHAP values for feature importance on a per-prediction basis.

## 17. Eligibility Filtering
Hard filters out courses based on strict age, education, and skill level constraints to prevent recommending impossible options.

## 18. Content-Based Fallback
A fallback heuristic weighted scoring model when the ML model is unavailable or encounters errors.

## 19. Replacing Synthetic Data with Real SIH Data
1. Replace CSVs in `data/raw/` with real data.
2. Align column names to `config/config.yaml`.
3. Rerun pipeline from `clean` step.

## 20. How to Run
```bash
python main.py --step all
python main.py --step predict
```

## 21. Project Structure
- `src/`: Source code.
- `data/`: Datasets.
- `models/`: Serialized models.
- `reports/`: Documentation.
- `main.py`: Entry point.

## 22. Requirements
- pandas, numpy, scikit-learn, shap, joblib

## 23. Reproducibility
Random seeds are fixed to 42 for synthetic generation and model training splits.
