# ml/collaborative_filter.py
"""
User-User Collaborative Filtering for Job Recommendations
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from ml.data_preprocessor import DataPreprocessor
from ml.config import MIN_COMMON_USERS, SIMILARITY_METHOD

class CollaborativeFilter:
    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.user_job_matrix = None
        self.user_similarity = None
        self.user_ids = None
        self.job_ids = None
    
    def build_user_job_matrix(self):
        """
        Build user-job rating matrix from application history
        """
        apps_df = self.preprocessor.load_user_applications()
        
        # Create pivot table
        self.user_job_matrix = apps_df.pivot_table(
            index='user_id',
            columns='job_id',
            values='rating',
            fill_value=0
        )
        
        self.user_ids = self.user_job_matrix.index.tolist()
        self.job_ids = self.user_job_matrix.columns.tolist()
        
        return self
    
    def calculate_user_similarity(self):
        """
        Calculate similarity between users
        """
        if self.user_job_matrix is None:
            self.build_user_job_matrix()
        
        # Calculate cosine similarity between users
        self.user_similarity = cosine_similarity(self.user_job_matrix)
        
        # Convert to DataFrame for easier access
        self.user_similarity_df = pd.DataFrame(
            self.user_similarity,
            index=self.user_ids,
            columns=self.user_ids
        )
        
        return self
    
    def find_similar_users(self, user_id, top_n=5):
        """
        Find top N similar users to given user
        """
        if self.user_similarity_df is None:
            self.calculate_user_similarity()
        
        if user_id not in self.user_similarity_df.index:
            return []
        
        similar_users = self.user_similarity_df[user_id].sort_values(ascending=False)
        similar_users = similar_users[similar_users.index != user_id]
        
        return similar_users.head(top_n).to_dict()
    
    def get_collaborative_recommendations(self, user_id, top_n=10):
        """
        Get job recommendations based on similar users
        """
        if self.user_job_matrix is None:
            self.build_user_job_matrix()
        
        similar_users = self.find_similar_users(user_id, top_n=5)
        
        if not similar_users:
            return []
        
        # Get jobs liked by similar users that target user hasn't applied to
        user_applied_jobs = set(
            self.user_job_matrix.loc[user_id][self.user_job_matrix.loc[user_id] > 0].index
        )
        
        job_scores = {}
        
        for sim_user, similarity_score in similar_users.items():
            if sim_user in self.user_job_matrix.index:
                user_ratings = self.user_job_matrix.loc[sim_user]
                
                for job_id, rating in user_ratings.items():
                    if job_id not in user_applied_jobs and rating > 0:
                        if job_id not in job_scores:
                            job_scores[job_id] = 0
                        job_scores[job_id] += similarity_score * rating
        
        # Sort by score
        sorted_jobs = sorted(job_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_jobs:
            return []
        
        # Get top N job IDs
        top_job_ids = [job_id for job_id, score in sorted_jobs[:top_n]]
        
        # Get job details
        jobs_df = self.preprocessor.load_all_jobs_with_skills()
        results = jobs_df[jobs_df['job_id'].isin(top_job_ids)]
        
        # Add collaborative score
        score_dict = dict(sorted_jobs)
        results['collab_score'] = results['job_id'].map(score_dict)
        results = results.sort_values('collab_score', ascending=False)
        
        return results.to_dict('records')