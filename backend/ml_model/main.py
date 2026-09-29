import argparse
import sys
import os
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if __package__ in (None, ''):
    sys.path.insert(0, os.path.dirname(PROJECT_ROOT))

def main():
    parser = argparse.ArgumentParser(description='PM-AJAY NSQ Course Recommendation Pipeline')
    parser.add_argument('--step', type=str, default='all',
                       choices=['all', 'generate', 'clean', 'eda', 'train', 'predict', 'predict_fallback'],
                       help='Pipeline step to run')
    parser.add_argument('--top-k', type=int, default=5, help='Number of top recommendations')
    args = parser.parse_args()
    
    start_time = time.time()
    
    if args.step in ['all', 'generate']:
        print('=' * 60)
        print('STEP 1: Generating synthetic data...')
        print('=' * 60)
        try:
            from ml_model.src.data_generation.generate_courses import generate_courses
            from ml_model.src.data_generation.generate_beneficiaries import generate_beneficiaries
            from ml_model.src.data_generation.generate_interactions import generate_interactions
            
            generate_courses()
            generate_beneficiaries()
            generate_interactions()
        except ImportError as e:
            print(f"Error importing generation modules: {e}")
    
    if args.step in ['all', 'clean']:
        print('=' * 60)
        print('STEP 2: Cleaning data...')
        print('=' * 60)
        try:
            from ml_model.src.preprocessing.clean import clean_beneficiary_data
            clean_beneficiary_data()
        except ImportError as e:
            print(f"Error importing cleaning module: {e}")
    
    if args.step in ['all', 'eda']:
        print('=' * 60)
        print('STEP 3: Running EDA...')
        print('=' * 60)
        try:
            from ml_model.src.eda.run_eda import run_eda
            run_eda()
        except ImportError as e:
            print(f"Error importing EDA module: {e}")
    
    if args.step in ['all', 'train']:
        print('=' * 60)
        print('STEP 4: Feature Engineering & Dataset Creation...')
        print('=' * 60)
        try:
            import pandas as pd
            from ml_model.src.feature_engineering.features import create_training_dataset
            beneficiaries = pd.read_csv(os.path.join(PROJECT_ROOT, 'data', 'cleaned', 'cleaned_beneficiary_data.csv'))
            courses = pd.read_csv(os.path.join(PROJECT_ROOT, 'data', 'reference', 'courses.csv'))
            interactions = pd.read_csv(os.path.join(PROJECT_ROOT, 'data', 'raw', 'historical_interactions.csv'))
            create_training_dataset(beneficiaries, courses, interactions, negative_ratio=3, seed=42)
            print("Feature dataset created successfully.")
        except Exception as e:
            print(f"Error in feature engineering: {e}")

        print('=' * 60)
        print('STEP 5: Training models...')
        print('=' * 60)
        try:
            from ml_model.src.training.train import train_models
            train_models()
        except Exception as e:
            print(f"Error importing/executing training module: {e}")
    
    if args.step in ['all', 'predict']:
        print('=' * 60)
        print('STEP 5: Running sample predictions...')
        print('=' * 60)
        try:
            from ml_model.src.prediction.predict import run_sample_predictions
            run_sample_predictions()
        except ImportError as e:
            print(f"Error importing prediction module: {e}")
    
    if args.step == 'predict_fallback':
        print('=' * 60)
        print('Running fallback predictions...')
        print('=' * 60)
        try:
            from ml_model.src.prediction.predict import run_sample_predictions_fallback
            run_sample_predictions_fallback()
        except ImportError as e:
            print(f"Error importing prediction module: {e}")
            
    print(f"\nPipeline finished in {time.time() - start_time:.2f} seconds.")

if __name__ == '__main__':
    main()
