# Scaling Strategy

## 1. Overview
Proper feature scaling is crucial for models sensitive to feature magnitudes, particularly distance-based models or regularized linear models, and can speed up convergence for tree-based models.

## 2. StandardScaler Features
| Feature | Distribution | Reason |
|---------|-------------|---------|
| `age` | Normal-ish | Standardizes to mean 0, unit variance |
| `work_experience_years` | Right-skewed | Brings within comparable range |

## 3. RobustScaler Features
| Feature | Outliers | Reason |
|---------|----------|---------|
| `annual_family_income` | High | Robust to extreme outliers in income |
| `distance_to_training_center_km` | Occasional extreme | Handles very far centers smoothly |

## 4. No Scaling Features
| Feature | Reason |
|---------|---------|
| `career_interest_match` | Binary [0, 1] |
| `skill_match_score` | Already bounded internally |
| `nsqf_appropriateness` | Already [0, 1] scaled internally |

## 5. Features NOT Scaled
Categorical embeddings, one-hot encoded variables, and ordinal features (like Education 0-6) remain unscaled to preserve their intrinsic discrete meaning.

## 6. Decision Process
Analyzed feature distributions in EDA. Variables with heavy tails received RobustScaler. Normally distributed continuous variables received StandardScaler.

## 7. Important Notes
Scalers are fitted strictly on the training set. The exact same transformations are applied to the test set and production inference data to prevent data leakage.
