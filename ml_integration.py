# ml_integration.py
"""
Bridge between Flask app and ML components
"""

from ml.hybrid_recommender import HybridRecommender
from ml.skill_matcher import SkillMatcher
from ml.data_preprocessor import DataPreprocessor

# Global instance (load once)
_hybrid_recommender = None
_skill_matcher = None

def get_hybrid_recommender():
    """Get or create hybrid recommender instance"""
    global _hybrid_recommender
    if _hybrid_recommender is None:
        _hybrid_recommender = HybridRecommender()
        _hybrid_recommender.load_models()
    return _hybrid_recommender

def get_skill_matcher():
    """Get or create skill matcher instance"""
    global _skill_matcher
    if _skill_matcher is None:
        _skill_matcher = SkillMatcher()
        _skill_matcher.load_data()
    return _skill_matcher

def get_ml_recommendations(user_id, method='hybrid'):
    """
    Get ML-powered recommendations
    
    Parameters:
    - user_id: Student ID
    - method: 'hybrid', 'skill_only', or 'collab_only'
    """
    if method == 'hybrid':
        recommender = get_hybrid_recommender()
        return recommender.get_hybrid_recommendations(user_id)
    elif method == 'skill_only':
        matcher = get_skill_matcher()
        return matcher.get_enhanced_recommendations(user_id)
    else:
        # collab_only - would need to implement
        return []