# ml/hybrid_recommender.py
"""
Hybrid Recommender that combines multiple recommendation methods
"""

import pandas as pd
from ml.skill_matcher import SkillMatcher
from ml.collaborative_filter import CollaborativeFilter
from ml.config import HYBRID_WEIGHTS, MAX_RECOMMENDATIONS

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
    
    def get_hybrid_recommendations(self, user_id):
        """
        Get recommendations using weighted hybrid approach
        """
        if not self.is_loaded:
            self.load_models()
        
        # Get skill-based recommendations
        skill_results = self.skill_matcher.calculate_match_scores(user_id)
        
        # Get collaborative recommendations
        collab_results = self.collaborative_filter.get_collaborative_recommendations(user_id)
        collab_df = pd.DataFrame(collab_results) if collab_results else pd.DataFrame()
        
        # Get job details
        preprocessor = self.skill_matcher.preprocessor
        all_jobs = preprocessor.load_all_jobs_with_skills()
        
        # Combine scores
        if not skill_results.empty:
            # Start with skill-based scores
            final_scores = skill_results.copy()
            final_scores['final_score'] = final_scores['ml_match_score'] * HYBRID_WEIGHTS['skill_match']
            
            # Add collaborative scores
            if not collab_df.empty:
                for _, row in collab_df.iterrows():
                    job_id = row['job_id']
                    if job_id in final_scores['job_id'].values:
                        idx = final_scores[final_scores['job_id'] == job_id].index[0]
                        final_scores.loc[idx, 'final_score'] += row.get('collab_score', 0) * HYBRID_WEIGHTS['collaborative']
                    else:
                        new_row = {'job_id': job_id, 'ml_match_score': 0, 'final_score': row.get('collab_score', 0) * HYBRID_WEIGHTS['collaborative']}
                        final_scores = pd.concat([final_scores, pd.DataFrame([new_row])], ignore_index=True)
            
            # Sort by final score
            final_scores = final_scores.sort_values('final_score', ascending=False)
            final_scores = final_scores.head(MAX_RECOMMENDATIONS)
            
            # Merge with job details
            results = all_jobs.merge(final_scores, on='job_id')
            results['match_score'] = results['final_score'].round(2)
            
            return results.to_dict('records')
        
        # Fallback to collaborative if skill matching fails
        return collab_results