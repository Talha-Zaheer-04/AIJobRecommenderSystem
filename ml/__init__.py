# ml/__init__.py
"""
ML Module for Job Recommendation System
Provides machine learning based job matching and recommendations
"""

import warnings
from typing import List, Dict, Any

# Suppress pandas warnings (optional)
warnings.filterwarnings('ignore', category=UserWarning)

# ==================== IMPORTS ====================

from ml.skill_matcher import SkillMatcher
from ml.collaborative_filter import CollaborativeFilter
from ml.hybrid_recommender import HybridRecommender
from ml.data_preprocessor import DataPreprocessor


# ==================== GLOBAL INSTANCES (Lazy Loading) ====================

_skill_matcher = None
_collaborative_filter = None
_hybrid_recommender = None


# ==================== MODEL GETTERS ====================

def get_skill_matcher() -> SkillMatcher:
    """
    Get or create SkillMatcher instance (singleton pattern)
    
    Returns:
        SkillMatcher instance with loaded data
    """
    global _skill_matcher
    if _skill_matcher is None:
        _skill_matcher = SkillMatcher()
        _skill_matcher.load_data()
    return _skill_matcher


def get_collaborative_filter() -> CollaborativeFilter:
    """
    Get or create CollaborativeFilter instance (singleton pattern)
    
    Returns:
        CollaborativeFilter instance with built matrices
    """
    global _collaborative_filter
    if _collaborative_filter is None:
        _collaborative_filter = CollaborativeFilter()
        _collaborative_filter.build_user_job_matrix()
        _collaborative_filter.calculate_user_similarity()
    return _collaborative_filter


def get_hybrid_recommender() -> HybridRecommender:
    """
    Get or create HybridRecommender instance (singleton pattern)
    
    Returns:
        HybridRecommender instance with loaded models
    """
    global _hybrid_recommender
    if _hybrid_recommender is None:
        _hybrid_recommender = HybridRecommender()
        _hybrid_recommender.load_models()
    return _hybrid_recommender


# ==================== MAIN RECOMMENDATION FUNCTION ====================

def get_ml_recommendations(user_id: int, method: str = 'hybrid') -> List[Dict[str, Any]]:
    """
    Get ML-powered job recommendations
    
    Parameters:
        user_id: Student ID
        method: Recommendation method - 'hybrid', 'skill_only', or 'collab_only'
    
    Returns:
        List of job dictionaries with match scores
    
    Examples:
        >>> recs = get_ml_recommendations(1, method='hybrid')
        >>> for job in recs:
        ...     print(job['title'], job['match_score'])
    """
    if method == 'hybrid':
        recommender = get_hybrid_recommender()
        recommendations = recommender.get_hybrid_recommendations(user_id)
    elif method == 'skill_only':
        matcher = get_skill_matcher()
        recommendations = matcher.get_enhanced_recommendations(user_id, limit=20)
    else:  # collab_only
        collab = get_collaborative_filter()
        recommendations = collab.get_collaborative_recommendations(user_id, top_n=20)
    
    return recommendations if recommendations else []


# ==================== UTILITY FUNCTIONS ====================

def refresh_all_models() -> None:
    """
    Force refresh all ML models (clears cached instances)
    Useful when new data is added to the database
    """
    global _skill_matcher, _collaborative_filter, _hybrid_recommender
    _skill_matcher = None
    _collaborative_filter = None
    _hybrid_recommender = None
    print("All ML models have been refreshed.")


def get_available_methods() -> Dict[str, str]:
    """
    Get available recommendation methods with descriptions
    
    Returns:
        Dictionary mapping method names to descriptions
    """
    return {
        'hybrid': 'Hybrid (Skill + Collaborative)',
        'skill_only': 'Skill-Based Only',
        'collab_only': 'Collaborative Filtering Only'
    }