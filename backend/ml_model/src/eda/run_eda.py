import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import traceback

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_eda(cleaned_path=None, courses_path=None, interactions_path=None, output_dir=None):
    if cleaned_path is None:
        cleaned_path = os.path.join(PROJECT_ROOT, 'data', 'cleaned', 'cleaned_beneficiary_data.csv')
    if courses_path is None:
        courses_path = os.path.join(PROJECT_ROOT, 'data', 'reference', 'courses.csv')
    if interactions_path is None:
        interactions_path = os.path.join(PROJECT_ROOT, 'data', 'raw', 'historical_interactions.csv')
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, 'reports', 'eda')

    os.makedirs(output_dir, exist_ok=True)

    print("Loading data...")
    try:
        ben_df = pd.read_csv(cleaned_path)
    except Exception as e:
        print(f"Could not load beneficiary data: {e}")
        return

    try:
        courses_df = pd.read_csv(courses_path)
    except Exception as e:
        print(f"Could not load courses data: {e}")
        courses_df = pd.DataFrame()

    try:
        inter_df = pd.read_csv(interactions_path)
    except Exception as e:
        print(f"Could not load interactions data: {e}")
        inter_df = pd.DataFrame()

    sns.set_theme(style="whitegrid", palette="Set2")
    plt.rcParams['figure.figsize'] = (10, 6)

    def save_plot(name):
        plt.savefig(os.path.join(output_dir, name), dpi=150, bbox_inches='tight')
        plt.close()

    print("Generating Univariate Analysis...")
    try:
        if 'age' in ben_df.columns:
            sns.histplot(ben_df['age'], kde=True)
            plt.title('Age Distribution')
            save_plot('01_age_distribution.png')
    except Exception as e: print(f"Failed plot 1: {e}")

    try:
        if 'annual_family_income' in ben_df.columns:
            sns.histplot(ben_df['annual_family_income'], log_scale=True)
            plt.title('Income Distribution')
            save_plot('02_income_distribution.png')
    except Exception as e: print(f"Failed plot 2: {e}")

    try:
        if 'education_level' in ben_df.columns:
            order = ['No_Formal', 'Primary', 'Middle', 'Secondary', 'Senior_Secondary', 'Graduate', 'Post_Graduate', 'Unknown']
            valid_order = [o for o in order if o in ben_df['education_level'].unique()]
            sns.countplot(y=ben_df['education_level'], order=valid_order)
            plt.title('Education Distribution')
            save_plot('03_education_distribution.png')
    except Exception as e: print(f"Failed plot 3: {e}")

    try:
        if 'gender' in ben_df.columns:
            ben_df['gender'].value_counts().plot.pie(autopct='%1.1f%%', colors=sns.color_palette("Set2"))
            plt.title('Gender Distribution')
            save_plot('04_gender_distribution.png')
    except Exception as e: print(f"Failed plot 4: {e}")

    try:
        if 'employment_status' in ben_df.columns:
            sns.countplot(x=ben_df['employment_status'])
            plt.title('Employment Distribution')
            plt.xticks(rotation=45)
            save_plot('05_employment_distribution.png')
    except Exception as e: print(f"Failed plot 5: {e}")

    try:
        skill_cols = ['digital_literacy', 'communication_skill', 'numerical_skill', 'technical_skill', 'entrepreneurial_skill']
        existing_skill_col = 'existing_skill_level'
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        for i, col in enumerate(skill_cols):
            if col in ben_df.columns:
                sns.histplot(ben_df[col], bins=10, ax=axes[i])
                axes[i].set_title(f'{col} Distribution')
        
        if existing_skill_col in ben_df.columns:
            sns.countplot(x=ben_df[existing_skill_col], ax=axes[5])
            axes[5].set_title('Existing Skill Level')
        
        plt.tight_layout()
        save_plot('06_skill_distributions.png')
    except Exception as e: print(f"Failed plot 6: {e}")

    try:
        if 'state' in ben_df.columns:
            top_states = ben_df['state'].value_counts().nlargest(15)
            sns.barplot(x=top_states.values, y=top_states.index)
            plt.title('Top 15 States Distribution')
            save_plot('07_state_distribution.png')
    except Exception as e: print(f"Failed plot 7: {e}")

    try:
        if 'social_category' in ben_df.columns:
            sns.countplot(x=ben_df['social_category'])
            plt.title('Social Category Distribution')
            save_plot('08_social_category_distribution.png')
    except Exception as e: print(f"Failed plot 8: {e}")

    try:
        if 'career_interest' in ben_df.columns:
            sns.countplot(y=ben_df['career_interest'], order=ben_df['career_interest'].value_counts().index)
            plt.title('Career Interest Distribution')
            save_plot('09_career_interest_distribution.png')
    except Exception as e: print(f"Failed plot 9: {e}")

    try:
        if 'rural_urban' in ben_df.columns:
            ben_df['rural_urban'].value_counts().plot.pie(autopct='%1.1f%%', colors=sns.color_palette("Set2"))
            plt.title('Rural vs Urban Distribution')
            save_plot('10_rural_urban_distribution.png')
    except Exception as e: print(f"Failed plot 10: {e}")

    print("Generating Bivariate Analysis...")
    merged_df = pd.DataFrame()
    if not courses_df.empty and not inter_df.empty and not ben_df.empty:
        try:
            merged_df = ben_df.merge(inter_df, on='beneficiary_id', how='inner')
            merged_df = merged_df.merge(courses_df, on='course_id', how='inner')
        except Exception as e:
            print(f"Merge failed: {e}")

    try:
        if not merged_df.empty and 'education_level' in merged_df.columns and 'sector' in merged_df.columns:
            plt.figure(figsize=(12, 8))
            ct = pd.crosstab(merged_df['education_level'], merged_df['sector'], normalize='index')
            ct.plot(kind='bar', stacked=True, colormap='Set2', figsize=(12, 8))
            plt.title('Education Level vs Enrolled Course Sector')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            save_plot('11_education_vs_course_sector.png')
    except Exception as e: print(f"Failed plot 11: {e}")

    try:
        if not merged_df.empty and 'nsqf_level' in merged_df.columns:
            skill_cols = ['digital_literacy', 'communication_skill', 'numerical_skill', 'technical_skill', 'entrepreneurial_skill']
            valid_cols = [c for c in skill_cols if c in merged_df.columns]
            if valid_cols:
                pivot = merged_df.groupby('nsqf_level')[valid_cols].mean()
                sns.heatmap(pivot, annot=True, cmap='YlGnBu')
                plt.title('Average Skill Scores per NSQF Level')
                save_plot('12_skills_vs_nsqf_level.png')
    except Exception as e: print(f"Failed plot 12: {e}")

    try:
        if not merged_df.empty and 'career_interest' in merged_df.columns and 'sector' in merged_df.columns:
            ct = pd.crosstab(merged_df['career_interest'], merged_df['sector'])
            plt.figure(figsize=(12, 10))
            sns.heatmap(ct, annot=True, fmt='d', cmap='YlGnBu')
            plt.title('Career Interest vs Course Sector Enrollment')
            save_plot('13_career_interest_vs_course.png')
    except Exception as e: print(f"Failed plot 13: {e}")

    try:
        if not inter_df.empty and not ben_df.empty and 'annual_family_income' in ben_df.columns:
            enrolled_users = inter_df[inter_df['enrolled'] == 1]['beneficiary_id'].unique() if 'enrolled' in inter_df.columns else []
            ben_df['is_enrolled'] = ben_df['beneficiary_id'].isin(enrolled_users)
            sns.boxplot(x='is_enrolled', y='annual_family_income', data=ben_df)
            plt.yscale('log')
            plt.title('Income by Enrollment Status')
            save_plot('14_income_vs_enrollment.png')
    except Exception as e: print(f"Failed plot 14: {e}")

    try:
        if 'distance_to_training_center_km' in ben_df.columns and 'is_enrolled' in ben_df.columns:
            sns.boxplot(x='is_enrolled', y='distance_to_training_center_km', data=ben_df)
            plt.title('Distance to Training Center vs Enrollment')
            save_plot('15_distance_vs_enrollment.png')
    except Exception as e: print(f"Failed plot 15: {e}")

    try:
        if not merged_df.empty and 'age' in merged_df.columns and 'nsqf_level' in merged_df.columns:
            sns.boxplot(x='nsqf_level', y='age', data=merged_df)
            plt.title('Age vs NSQF Level of Enrolled Courses')
            save_plot('16_age_vs_course_nsqf.png')
    except Exception as e: print(f"Failed plot 16: {e}")

    print("Generating Target Analysis...")
    try:
        if not merged_df.empty and 'course_name' in merged_df.columns:
            top_courses = merged_df['course_name'].value_counts().nlargest(20)
            sns.barplot(x=top_courses.values, y=top_courses.index)
            plt.title('Top 20 Most Popular Courses')
            save_plot('17_course_popularity.png')
    except Exception as e: print(f"Failed plot 17: {e}")

    try:
        if not merged_df.empty and 'outcome' in merged_df.columns:
            sns.countplot(x='outcome', data=merged_df)
            plt.title('Outcome Distribution')
            save_plot('18_outcome_distribution.png')
    except Exception as e: print(f"Failed plot 18: {e}")

    try:
        if not merged_df.empty and 'sector' in merged_df.columns and 'outcome' in merged_df.columns:
            outcome_rates = merged_df.groupby('sector')['outcome'].mean().sort_values(ascending=False)
            sns.barplot(x=outcome_rates.values, y=outcome_rates.index)
            plt.title('Outcome Rate by Sector')
            plt.xlabel('Positive Outcome Rate')
            save_plot('19_sector_outcome_rates.png')
    except Exception as e: print(f"Failed plot 19: {e}")

    print("Generating Correlation Analysis...")
    try:
        num_cols = ben_df.select_dtypes(include=[np.number]).columns
        corr = ben_df[num_cols].corr()
        plt.figure(figsize=(15, 12))
        sns.heatmap(corr, annot=False, cmap='coolwarm', center=0)
        plt.title('Correlation Heatmap')
        save_plot('20_correlation_heatmap.png')
    except Exception as e: print(f"Failed plot 20: {e}")

    try:
        if 'local_job_demand' in ben_df.columns:
            sns.countplot(x='local_job_demand', data=ben_df)
            plt.title('Local Job Demand Distribution')
            save_plot('21_local_demand_distribution.png')
    except Exception as e: print(f"Failed plot 21: {e}")

    try:
        if 'preferred_training_mode' in ben_df.columns:
            sns.countplot(x='preferred_training_mode', data=ben_df)
            plt.title('Preferred Training Mode Distribution')
            save_plot('22_training_mode_preference.png')
    except Exception as e: print(f"Failed plot 22: {e}")

    print("Generating EDA summary report...")
    try:
        report_path = os.path.join(output_dir, 'eda_summary_report.md')
        with open(report_path, 'w') as f:
            f.write("# EDA Summary Report\n\n")
            f.write("## Dataset Overview\n")
            f.write(f"- Cleaned Beneficiary Data Shape: {ben_df.shape}\n")
            f.write(f"- Courses Data Shape: {courses_df.shape}\n")
            f.write(f"- Interactions Data Shape: {inter_df.shape}\n\n")
            f.write("## Key Findings\n")
            f.write("- **Univariate**: Basic distributions generated successfully.\n")
            f.write("- **Bivariate**: Relationships between demographics and enrollment analyzed.\n")
            f.write("- **Target Analysis**: Most popular courses and sector-wise outcomes explored.\n")
            f.write("- **Correlation**: Identified relationships between numerical features.\n\n")
            f.write("## Recommendations for Modeling\n")
            f.write("- Use identified correlations for feature selection.\n")
            f.write("- Address class imbalance in target variables if any.\n")
            f.write("- Leverage feature engineering based on strong bivariate relationships.\n")
        print(f"Saved EDA report to {report_path}")
    except Exception as e:
        print(f"Failed to write report: {e}")

if __name__ == '__main__':
    run_eda()
