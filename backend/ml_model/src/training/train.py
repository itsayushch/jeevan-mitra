import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, RobustScaler, OrdinalEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupShuffleSplit, RandomizedSearchCV, GroupKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score
from sklearn.base import BaseEstimator, TransformerMixin, clone

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import lightgbm as lgb

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Features to use for model training
TARGET = 'outcome'
GROUP_COL = 'beneficiary_id'
ID_COL = 'course_id'

EXCLUDE_COLS = [TARGET, GROUP_COL, ID_COL]

NUMERICAL_FEATURES = [
    'age', 'annual_family_income', 'work_experience_years',
    'digital_literacy', 'communication_skill', 'numerical_skill',
    'technical_skill', 'entrepreneurial_skill',
    'distance_to_training_center_km', 'previous_training_count',
    'training_completion_rate', 'course_duration_hours', 'average_salary',
    'nsqf_level',
    'skill_match_score', 'distance_penalty', 'nsqf_appropriateness',
    'experience_relevance', 'local_demand_score'
]

STANDARD_SCALE = [
    'age', 'digital_literacy', 'communication_skill', 'numerical_skill',
    'technical_skill', 'entrepreneurial_skill', 'previous_training_count',
    'nsqf_level', 'course_duration_hours', 'average_salary'
]

ROBUST_SCALE = [
    'annual_family_income', 'work_experience_years',
    'distance_to_training_center_km'
]

NO_SCALE = [
    'skill_match_score', 'distance_penalty', 'nsqf_appropriateness',
    'experience_relevance', 'local_demand_score', 'training_completion_rate'
]

ORDINAL_FEATURES = {
    'education_level': ['No_Formal', 'Primary', 'Middle', 'Secondary', 'Senior_Secondary', 'Graduate', 'Post_Graduate'],
    'existing_skill_level': ['Beginner', 'Intermediate', 'Advanced', 'Expert'],
    'preferred_duration': ['Short', 'Medium', 'Long'],
    'required_skill_level': ['Beginner', 'Intermediate', 'Advanced'],
    'local_job_demand': ['Low', 'Medium', 'High'],
    'local_demand': ['Low', 'Medium', 'High', 'Very_High'],
}

NOMINAL_FEATURES = [
    'gender', 'social_category', 'employment_status', 'rural_urban',
    'preferred_work_type', 'preferred_training_mode', 'delivery_mode'
]

HIGH_CARDINALITY_FEATURES = [
    'state', 'district', 'current_occupation', 'local_industry',
    'sector', 'career_interest'
]

BINARY_FEATURES = [
    'career_interest_match', 'education_eligibility', 'industry_match',
    'language_match', 'age_eligibility', 'training_mode_match'
]

from ml_model.src.feature_engineering.encoders import FrequencyEncoder

def compute_ranking_metrics(y_true, y_scores, beneficiary_ids, course_ids, k_values=[3, 5, 10]):
    """Compute ranking metrics per beneficiary, then average."""
    df = pd.DataFrame({
        'b_id': beneficiary_ids,
        'c_id': course_ids,
        'y_true': y_true,
        'y_score': y_scores
    })
    
    metrics = {f'HitRate@{k}': [] for k in k_values}
    for k in k_values:
        metrics[f'Precision@{k}'] = []
        metrics[f'Recall@{k}'] = []
        metrics[f'NDCG@{k}'] = []
    metrics['MRR'] = []

    for _, group in df.groupby('b_id'):
        group = group.sort_values('y_score', ascending=False).reset_index(drop=True)
        y_t = group['y_true'].values
        total_relevant = y_t.sum()
        
        if total_relevant == 0:
            continue
            
        for k in k_values:
            top_k = y_t[:k]
            hits = top_k.sum()
            metrics[f'HitRate@{k}'].append(1 if hits > 0 else 0)
            metrics[f'Precision@{k}'].append(hits / k)
            metrics[f'Recall@{k}'].append(hits / total_relevant)
            
            dcg = sum((2**rel - 1) / np.log2(i + 2) for i, rel in enumerate(top_k))
            idcg = sum((2**rel - 1) / np.log2(i + 2) for i, rel in enumerate(sorted(y_t, reverse=True)[:k]))
            metrics[f'NDCG@{k}'].append(dcg / idcg if idcg > 0 else 0)
            
        # MRR
        ranks = np.where(y_t == 1)[0]
        if len(ranks) > 0:
            metrics['MRR'].append(1.0 / (ranks[0] + 1))
        else:
            metrics['MRR'].append(0.0)
            
    return {k: np.mean(v) if v else 0.0 for k, v in metrics.items()}

def train_models(data_path=None, config_path=None):
    if data_path is None:
        data_path = os.path.join(PROJECT_ROOT, 'data', 'processed', 'processed_beneficiary_data.csv')
    
    print(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Fill missing columns if any
    for col in STANDARD_SCALE + ROBUST_SCALE + NO_SCALE + NOMINAL_FEATURES + HIGH_CARDINALITY_FEATURES + BINARY_FEATURES:
        if col not in df.columns:
            df[col] = np.nan
    for col in ORDINAL_FEATURES:
        if col not in df.columns:
            df[col] = 'Unknown'
            
    # Train/Val/Test Split
    gss1 = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_val_idx, test_idx = next(gss1.split(df, groups=df[GROUP_COL]))
    
    train_val_df = df.iloc[train_val_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)
    
    gss2 = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42) # 0.25 of 0.8 is 0.2
    train_idx, val_idx = next(gss2.split(train_val_df, groups=train_val_df[GROUP_COL]))
    
    train_df = train_val_df.iloc[train_idx].reset_index(drop=True)
    val_df = train_val_df.iloc[val_idx].reset_index(drop=True)
    
    os.makedirs(os.path.join(PROJECT_ROOT, 'data', 'processed'), exist_ok=True)
    train_df.to_csv(os.path.join(PROJECT_ROOT, 'data', 'processed', 'train.csv'), index=False)
    val_df.to_csv(os.path.join(PROJECT_ROOT, 'data', 'processed', 'validation.csv'), index=False)
    test_df.to_csv(os.path.join(PROJECT_ROOT, 'data', 'processed', 'test.csv'), index=False)
    
    print(f"Train size: {len(train_df)}, Val size: {len(val_df)}, Test size: {len(test_df)}")
    
    def build_preprocessor():
        standard_pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])

        robust_pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', RobustScaler())
        ])

        no_scale_pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='median'))
        ])

        ordinal_pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('encoder', OrdinalEncoder(
                categories=[ORDINAL_FEATURES[f] for f in ORDINAL_FEATURES.keys()],
                handle_unknown='use_encoded_value',
                unknown_value=-1
            ))
        ])

        nominal_pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='constant', fill_value='Unknown')),
            ('encoder', OneHotEncoder(
                handle_unknown='ignore',
                sparse_output=False,
                max_categories=15
            ))
        ])

        high_cardinality_pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='constant', fill_value='Unknown')),
            ('encoder', FrequencyEncoder())
        ])

        binary_pipeline = 'passthrough'

        return ColumnTransformer(
            transformers=[
                ('standard', standard_pipeline, STANDARD_SCALE),
                ('robust', robust_pipeline, ROBUST_SCALE),
                ('no_scale', no_scale_pipeline, NO_SCALE),
                ('ordinal', ordinal_pipeline, list(ORDINAL_FEATURES.keys())),
                ('nominal', nominal_pipeline, NOMINAL_FEATURES),
                ('high_card', high_cardinality_pipeline, HIGH_CARDINALITY_FEATURES),
                ('binary', binary_pipeline, BINARY_FEATURES)
            ],
            remainder='drop'
        )

    # Define models
    models = {
        'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'),
        'RandomForest': RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, class_weight='balanced', n_jobs=-1),
        'XGBoost': xgb.XGBClassifier(
            n_estimators=300, max_depth=8, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, eval_metric='logloss',
            n_jobs=-1
        ),
        'LightGBM': lgb.LGBMClassifier(
            n_estimators=300, max_depth=8, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, verbose=-1, n_jobs=-1,
            class_weight='balanced'
        )
    }

    X_train, y_train = train_df.drop(columns=[TARGET]), train_df[TARGET]
    X_val, y_val = val_df.drop(columns=[TARGET]), val_df[TARGET]
    X_test, y_test = test_df.drop(columns=[TARGET]), test_df[TARGET]

    b_id_val = val_df[GROUP_COL]
    c_id_val = val_df[ID_COL]

    results = {}
    best_model_name = None
    best_auc = -1
    trained_pipelines = {}
    for name, model in models.items():
        print(f"Training {name}...")
        pipeline = Pipeline([
            ('preprocessor', build_preprocessor()),
            ('model', model)
        ])
        
        pipeline.fit(X_train, y_train)
        trained_pipelines[name] = pipeline
        
        y_val_pred_proba = pipeline.predict_proba(X_val)[:, 1]
        y_val_pred = pipeline.predict(X_val)
        
        auc = roc_auc_score(y_val, y_val_pred_proba)
        pr_auc = average_precision_score(y_val, y_val_pred_proba)
        
        ranking_metrics = compute_ranking_metrics(y_val.values, y_val_pred_proba, b_id_val.values, c_id_val.values)
        
        results[name] = {
            'Accuracy': accuracy_score(y_val, y_val_pred),
            'Precision': precision_score(y_val, y_val_pred, zero_division=0),
            'Recall': recall_score(y_val, y_val_pred, zero_division=0),
            'F1': f1_score(y_val, y_val_pred, zero_division=0),
            'ROC-AUC': auc,
            'PR-AUC': pr_auc,
            **ranking_metrics
        }
        
        if auc > best_auc:
            best_auc = auc
            best_model_name = name
            
    print(f"Best model: {best_model_name} with ROC-AUC: {best_auc:.4f}")
    
    # Feature Importance for best model (assuming tree-based for XGB/LGB/RF)
    best_pipeline = trained_pipelines[best_model_name]
    best_model = best_pipeline.named_steps['model']
    best_preprocessor = best_pipeline.named_steps['preprocessor']
    
    # Extract feature names after preprocessing
    feature_names = []
    # Simplified feature name extraction
    for name, trans, cols in best_preprocessor.transformers_:
        if trans == 'drop': continue
        if name == 'binary':
            feature_names.extend(cols)
        elif name == 'ordinal' or name == 'high_card' or name == 'robust' or name == 'standard' or name == 'no_scale':
            feature_names.extend(cols)
        elif name == 'nominal':
            encoder = trans.named_steps['encoder']
            feature_names.extend(encoder.get_feature_names_out(cols))
            
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
        if len(importances) == len(feature_names):
            feat_imp = pd.Series(importances, index=feature_names).sort_values(ascending=False).head(30)
            
            os.makedirs(os.path.join(PROJECT_ROOT, 'reports'), exist_ok=True)
            plt.figure(figsize=(10, 8))
            feat_imp.plot(kind='barh')
            plt.title(f'Top 30 Feature Importances ({best_model_name})')
            plt.gca().invert_yaxis()
            plt.tight_layout()
            plt.savefig(os.path.join(PROJECT_ROOT, 'reports', 'feature_importance.png'))
            plt.close()
            
    # Save artifacts
    models_dir = os.path.join(PROJECT_ROOT, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    joblib.dump(best_pipeline, os.path.join(models_dir, 'best_model.pkl'))
    joblib.dump(best_preprocessor, os.path.join(models_dir, 'preprocessing_pipeline.pkl'))
    
    with open(os.path.join(models_dir, 'model_comparison.json'), 'w') as f:
        json.dump(results, f, indent=4)
        
    print(pd.DataFrame(results).T)

if __name__ == '__main__':
    train_models()
