# ml/collaborative_filter.py
"""
User-User Collaborative Filtering for Job Recommendations
Recommends jobs based on what similar users have applied to
"""

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional
from ml.data_preprocessor import DataPreprocessor
from ml.config import MIN_COMMON_USERS, SIMILARITY_METHOD


class CollaborativeFilter:
    """
    Collaborative filtering using user-user similarity
    Finds similar users based on their job application history
    """
    
    def __init__(self):
        """Initialize with data preprocessor"""
        self.preprocessor = DataPreprocessor()
        self.user_job_matrix: Optional[pd.DataFrame] = None
        self.user_similarity_df: Optional[pd.DataFrame] = None
        self.user_ids: Optional[List[int]] = None
        self.job_ids: Optional[List[int]] = None
    
    # ==================== MATRIX BUILDING ====================
    
    def build_user_job_matrix(self):
        """
        Build user-job rating matrix from application history
        
        Returns:
            self for method chaining
        """
        apps_df = self.preprocessor.load_user_applications()
        
        if apps_df.empty:
            self.user_job_matrix = pd.DataFrame()
            return self
        
        # Create pivot table: users as rows, jobs as columns, ratings as values
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
        Calculate cosine similarity between all users
        
        Returns:
            self for method chaining
        """
        if self.user_job_matrix is None or self.user_job_matrix.empty:
            self.build_user_job_matrix()
        
        if self.user_job_matrix.empty:
            self.user_similarity_df = pd.DataFrame()
            return self
        
        # Calculate cosine similarity between users
        similarity_matrix = cosine_similarity(self.user_job_matrix)
        
        # Convert to DataFrame for easier access
        self.user_similarity_df = pd.DataFrame(
            similarity_matrix,
            index=self.user_ids,
            columns=self.user_ids
        )
        
        return self
    
    # ==================== SIMILARITY SEARCH ====================
    
    def find_similar_users(self, user_id: int, top_n: int = 5) -> Dict[int, float]:
        """
        Find top N similar users to given user
        
        Args:
            user_id: Target user ID
            top_n: Number of similar users to return
        
        Returns:
            Dictionary mapping user_id to similarity score
        """
        if self.user_similarity_df is None or self.user_similarity_df.empty:
            self.calculate_user_similarity()
        
        if self.user_similarity_df.empty or user_id not in self.user_similarity_df.index:
            return {}
        
        # Get similarity scores for this user, excluding self
        similar_users = self.user_similarity_df[user_id].sort_values(ascending=False)
        similar_users = similar_users[similar_users.index != user_id]
        
        # Return top N
        return similar_users.head(top_n).to_dict()
    
    # ==================== RECOMMENDATION ENGINE ====================
    
    def get_collaborative_recommendations(self, user_id: int, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get job recommendations based on similar users' preferences
        
        Algorithm:
        1. Find users similar to target user
        2. Identify jobs they applied to (with rating > 0)
        3. Score jobs by weighted sum of similarity × rating
        4. Return top N jobs not already applied to by target user
        
        Args:
            user_id: Target user ID
            top_n: Maximum number of recommendations to return
        
        Returns:
            List of job dictionaries with collab_score
        """
        if self.user_job_matrix is None or self.user_job_matrix.empty:
            self.build_user_job_matrix()
        
        if self.user_job_matrix.empty:
            return []
        
        # Find similar users
        similar_users = self.find_similar_users(user_id, top_n=5)
        
        if not similar_users:
            return []
        
        # Get jobs already applied to by target user
        user_applied_jobs = set(
            self.user_job_matrix.loc[user_id][self.user_job_matrix.loc[user_id] > 0].index
        )
        
        # Calculate scores for candidate jobs
        job_scores: Dict[int, float] = {}
        
        for sim_user, similarity_score in similar_users.items():
            if sim_user not in self.user_job_matrix.index:
                continue
                
            user_ratings = self.user_job_matrix.loc[sim_user]
            
            for job_id, rating in user_ratings.items():
                # Skip jobs already applied to by target user
                if job_id in user_applied_jobs:
                    continue
                if rating <= 0:
                    continue
                    
                # Weighted sum: similarity × rating
                job_scores[job_id] = job_scores.get(job_id, 0) + similarity_score * rating
        
        # Sort by score and get top N
        sorted_jobs = sorted(job_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_jobs:
            return []
        
        top_job_ids = [job_id for job_id, _ in sorted_jobs[:top_n]]
        
        # Get job details
        jobs_df = self.preprocessor.load_all_jobs_with_skills()
        results = jobs_df[jobs_df['job_id'].isin(top_job_ids)].copy()
        
        # Add collaborative score
        score_dict = dict(sorted_jobs)
        results['collab_score'] = results['job_id'].map(score_dict)
        results = results.sort_values('collab_score', ascending=False)
        
        return results.to_dict('records')
    
    # ==================== UTILITY METHODS ====================
    
    def get_user_recommendation_score(self, user_id: int, job_id: int) -> float:
        """
        Get collaborative filtering score for a specific user-job pair
        
        Args:
            user_id: Student ID
            job_id: Job ID
        
        Returns:
            Collaborative filtering score (0 if no similar users)
        """
        similar_users = self.find_similar_users(user_id, top_n=5)
        
        if not similar_users:
            return 0.0
        
        score = 0.0
        for sim_user, similarity_score in similar_users.items():
            if sim_user in self.user_job_matrix.index:
                rating = self.user_job_matrix.loc[sim_user].get(job_id, 0)
                score += similarity_score * rating
        
        return round(score, 2)
    
    def has_sufficient_data(self) -> bool:
        """
        Check if there's enough data for collaborative filtering
        
        Returns:
            True if at least 2 users have application history
        """
        if self.user_job_matrix is None or self.user_job_matrix.empty:
            return False
        
        # Count users with at least one application
        users_with_apps = (self.user_job_matrix.sum(axis=1) > 0).sum()
        return users_with_apps >= MIN_COMMON_USERS