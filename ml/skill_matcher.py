# ml/skill_matcher.py
"""
Enhanced skill-based matching using cosine similarity
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from ml.data_preprocessor import DataPreprocessor
from ml.config import SKILL_MATCH_THRESHOLD

class SkillMatcher:
    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.user_skill_matrix = None
        self.job_skill_matrix = None
        self.skill_names = None
    
    def load_data(self):
        """Load and prepare skill matrices"""
        self.user_skill_matrix = self.preprocessor.load_user_skill_matrix()
        self.job_skill_matrix = self.preprocessor.load_job_skill_matrix()
        
        # Align skill columns
        common_skills = self.user_skill_matrix.columns.intersection(
            self.job_skill_matrix.columns
        )
        self.user_skill_matrix = self.user_skill_matrix[common_skills]
        self.job_skill_matrix = self.job_skill_matrix[common_skills]
        
        self.skill_names = common_skills.tolist()
        
        return self
    
    def calculate_match_scores(self, user_id):
        """
        Calculate cosine similarity between user and all jobs
        """
        if self.user_skill_matrix is None:
            self.load_data()
        
        # Get user vector
        if user_id not in self.user_skill_matrix.index:
            return pd.Series(dtype=float)
        
        user_vector = self.user_skill_matrix.loc[user_id].values.reshape(1, -1)
        
        # Get all job vectors
        job_vectors = self.job_skill_matrix.values
        
        # Calculate cosine similarity
        similarities = cosine_similarity(user_vector, job_vectors)[0]
        
        # Create results DataFrame
        results = pd.DataFrame({
            'job_id': self.job_skill_matrix.index,
            'ml_match_score': similarities * 100  # Convert to percentage
        })
        
        # Filter by threshold
        results = results[results['ml_match_score'] >= SKILL_MATCH_THRESHOLD]
        results = results.sort_values('ml_match_score', ascending=False)
        
        return results
    
    def get_enhanced_recommendations(self, user_id, limit=10):
        """
        Get enhanced skill-based recommendations
        """
        scores = self.calculate_match_scores(user_id)
        
        if scores.empty:
            return []
        
        # Get job details
        preprocessor = DataPreprocessor()
        jobs_df = preprocessor.load_all_jobs_with_skills()
        
        # Merge with scores
        results = jobs_df.merge(scores, on='job_id')
        results = results.head(limit)
        
        return results.to_dict('records')