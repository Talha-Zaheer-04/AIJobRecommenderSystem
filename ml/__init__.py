# ml/__init__.py
"""
ML Module for Job Recommendation System
"""

import warnings
warnings.filterwarnings('ignore', category=UserWarning)

from ml.skill_matcher import SkillMatcher
from ml.collaborative_filter import CollaborativeFilter
from ml.hybrid_recommender import HybridRecommender
from ml.data_preprocessor import DataPreprocessor

# Global instances (lazy loading)
_skill_matcher = None
_collaborative_filter = None
_hybrid_recommender = None

def get_skill_matcher():
    """Get or create SkillMatcher instance"""
    global _skill_matcher
    if _skill_matcher is None:
        _skill_matcher = SkillMatcher()
        _skill_matcher.load_data()
    return _skill_matcher

def get_collaborative_filter():
    """Get or create CollaborativeFilter instance"""
    global _collaborative_filter
    if _collaborative_filter is None:
        _collaborative_filter = CollaborativeFilter()
        _collaborative_filter.build_user_job_matrix()
        _collaborative_filter.calculate_user_similarity()
    return _collaborative_filter

def get_hybrid_recommender():
    """Get or create HybridRecommender instance"""
    global _hybrid_recommender
    if _hybrid_recommender is None:
        _hybrid_recommender = HybridRecommender()
        _hybrid_recommender.load_models()
    return _hybrid_recommender

def get_ml_recommendations(user_id, method='hybrid'):
    """
    Main function to get ML recommendations
    
    Parameters:
    - user_id: Student ID
    - method: 'hybrid', 'skill_only', or 'collab_only'
    
    Returns:
    - List of job dictionaries with match scores
    """
    if method == 'hybrid':
        recommender = get_hybrid_recommender()
        recommendations = recommender.get_hybrid_recommendations(user_id)
    elif method == 'skill_only':
        matcher = get_skill_matcher()
        recommendations = matcher.get_enhanced_recommendations(user_id, limit=20)
    else:
        # collab_only
        collab = get_collaborative_filter()
        recommendations = collab.get_collaborative_recommendations(user_id, top_n=20)
    
    return recommendations if recommendations else []