# ml/hybrid_recommender.py
"""
Hybrid Recommender with multiple recommendation strategies
"""

import pandas as pd
import numpy as np
from ml.skill_matcher import SkillMatcher
from ml.collaborative_filter import CollaborativeFilter
from ml.config import RECOMMENDATION_STRATEGIES, MAX_RECOMMENDATIONS

class HybridRecommender:
    def __init__(self):
        self.skill_matcher = SkillMatcher()
        self.collaborative_filter = CollaborativeFilter()
        self.is_loaded = False
    
    def load_models(self):
        """Load all models"""
        self.skill_matcher.load_data()
        self.collaborative_filter.build_user_job_matrix()
        self.collaborative_filter.calculate_user_similarity()
        self.is_loaded = True
        return self
    
    def get_recommendations_by_strategy(self, user_id, strategy='pure_skill'):
        """
        Get recommendations based on selected strategy
        
        Strategies:
        - pure_skill: 100% skill matching
        - balanced: 50% skill, 30% collaborative, 20% popularity
        - community: 30% skill, 60% collaborative, 10% popularity
        - trending: 20% skill, 20% collaborative, 60% popularity
        """
        if not self.is_loaded:
            self.load_models()
        
        weights = RECOMMENDATION_STRATEGIES.get(strategy, RECOMMENDATION_STRATEGIES['pure_skill'])['weights']
        
        # Get skill-based recommendations (already calculated and sorted)
        skill_recommendations = self.skill_matcher.get_enhanced_recommendations(user_id, limit=MAX_RECOMMENDATIONS)
        
        # Create DataFrame from skill recommendations
        if not skill_recommendations:
            return []
        
        skill_df = pd.DataFrame(skill_recommendations)
        skill_df = skill_df.rename(columns={'ml_match_score': 'skill_score'})
        skill_df['skill_score'] = skill_df['skill_score'].fillna(0)
        
        # Get collaborative scores (0-100)
        collab_results = self.collaborative_filter.get_collaborative_recommendations(user_id)
        collab_df = pd.DataFrame(collab_results) if collab_results else pd.DataFrame()
        if not collab_df.empty:
            collab_df = collab_df.rename(columns={'collab_score': 'collab_score'})
        
        # Get popularity scores (based on total applications per job)
        popularity_scores = self._get_popularity_scores()
        
        # Get all jobs for additional details
        all_jobs = self.skill_matcher.preprocessor.load_all_jobs_with_skills()
        
        # Start with skill scores
        final_scores = skill_df[['job_id', 'skill_score']].copy()
        final_scores['collab_score'] = 0
        final_scores['popularity_score'] = 0
        final_scores['final_score'] = final_scores['skill_score'] * weights['skill_match']
        
        # Add collaborative scores
        if not collab_df.empty:
            for _, row in collab_df.iterrows():
                job_id = row['job_id']
                if job_id in final_scores['job_id'].values:
                    idx = final_scores[final_scores['job_id'] == job_id].index[0]
                    final_scores.loc[idx, 'collab_score'] = row.get('collab_score', 0)
                    final_scores.loc[idx, 'final_score'] += row.get('collab_score', 0) * weights['collaborative']
                else:
                    # Add new job from collaborative results
                    new_row = pd.DataFrame([{
                        'job_id': job_id,
                        'skill_score': 0,
                        'collab_score': row.get('collab_score', 0),
                        'popularity_score': 0,
                        'final_score': row.get('collab_score', 0) * weights['collaborative']
                    }])
                    final_scores = pd.concat([final_scores, new_row], ignore_index=True)
        
        # Add popularity scores
        if not popularity_scores.empty:
            for _, row in popularity_scores.iterrows():
                job_id = row['job_id']
                if job_id in final_scores['job_id'].values:
                    idx = final_scores[final_scores['job_id'] == job_id].index[0]
                    final_scores.loc[idx, 'popularity_score'] = row['popularity_score']
                    final_scores.loc[idx, 'final_score'] += row['popularity_score'] * weights['popularity']
        
        # Sort by final score
        final_scores = final_scores.sort_values('final_score', ascending=False)
        final_scores = final_scores.head(MAX_RECOMMENDATIONS)
        
        # Merge with job details
        results = all_jobs.merge(final_scores, on='job_id')
        results['match_score'] = results['final_score'].round(1)
        
        # Add strategy info and ensure required fields
        results['recommendation_type'] = RECOMMENDATION_STRATEGIES[strategy]['name']
        
        # Convert to dictionary format matching what the template expects
        output = []
        for _, row in results.iterrows():
            output.append({
                'job_id': row['job_id'],
                'title': row['title'],
                'company_name': row['company_name'],
                'location': row['location'],
                'description': row['description'],
                'min_experience': row['min_experience'],
                'salary_min': row['salary_min'],
                'salary_max': row['salary_max'],
                'required_skills': row.get('required_skills', ''),
                'match_score': row['match_score'],
                'ml_match_score': row['skill_score'],
                'recommendation_type': row['recommendation_type']
            })
        
        return output
    
    def _get_popularity_scores(self):
        """Calculate popularity score for each job based on application count"""
        conn = self.skill_matcher.preprocessor.get_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            # Get max application count
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM Applications GROUP BY job_id ORDER BY cnt DESC LIMIT 1")
            max_result = cursor.fetchone()
            max_count = max_result[0] if max_result else 1
            cursor.close()
            
            # Calculate popularity scores
            query = """
            SELECT 
                j.job_id,
                COUNT(a.application_id) as application_count,
                (COUNT(a.application_id) * 1.0 / %s) * 100 as popularity_score
            FROM Jobs j
            LEFT JOIN Applications a ON j.job_id = a.job_id
            GROUP BY j.job_id
            """
            
            df = pd.read_sql(query, conn, params=[max_count])
            conn.close()
            
            df['popularity_score'] = df['popularity_score'].fillna(0)
            
        except Exception as e:
            print(f"Error calculating popularity scores: {e}")
            conn.close()
            return pd.DataFrame()
        
        return df[['job_id', 'popularity_score']]
    
    def get_hybrid_recommendations(self, user_id):
        """Legacy method - defaults to pure_skill"""
        return self.get_recommendations_by_strategy(user_id, 'pure_skill')