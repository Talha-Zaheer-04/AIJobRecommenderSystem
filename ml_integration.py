# ml_integration.py
"""
Bridge between Flask app and ML components
Handles recommendation strategies and model lifecycle
"""

from ml.hybrid_recommender import HybridRecommender
from ml.config import RECOMMENDATION_STRATEGIES

# ==================== GLOBAL INSTANCE ====================

_hybrid_recommender = None


# ==================== MODEL MANAGEMENT ====================

def get_hybrid_recommender():
    """Get or create hybrid recommender instance (singleton pattern)"""
    global _hybrid_recommender
    if _hybrid_recommender is None:
        _hybrid_recommender = HybridRecommender()
        _hybrid_recommender.load_models()
    return _hybrid_recommender


def refresh_ml_models():
    """Force refresh of ML models (clears cached instance)"""
    global _hybrid_recommender
    _hybrid_recommender = None
    return {"status": "success", "message": "Models will reload on next request"}


# ==================== RECOMMENDATION STRATEGIES ====================

RECOMMENDATION_STRATEGIES_MAP = {
    'pure_skill': '🎯 Skill Based',
    'balanced': '⚖️ Balanced',
    'community': '👥 Social Recommendation',
    'trending': '🔥 Trending'
}

STRATEGY_DESCRIPTIONS = {
    'pure_skill': 'Based purely on your skills matching job requirements',
    'balanced': '50% Skills + 30% Similar Users + 20% Popular Jobs',
    'community': 'Based on what similar students applied to',
    'trending': 'Popular jobs that many students are applying to'
}


def get_recommendation_strategies():
    """Return available recommendation strategies with display names"""
    return RECOMMENDATION_STRATEGIES_MAP.copy()


def get_strategy_description(strategy):
    """Get description for a specific strategy"""
    return STRATEGY_DESCRIPTIONS.get(strategy, '')


# ==================== CORE RECOMMENDATION FUNCTION ====================

def get_recommendations(user_id, strategy='pure_skill', limit=10):
    """
    Get ML-powered recommendations for a student
    
    Args:
        user_id: Student's user ID
        strategy: 'pure_skill', 'balanced', 'community', 'trending'
        limit: Max number of recommendations to return
    
    Returns:
        List of job recommendations with match scores
    """
    recommender = get_hybrid_recommender()
    recommendations = recommender.get_recommendations_by_strategy(user_id, strategy=strategy)
    
    # Apply limit
    if limit and len(recommendations) > limit:
        recommendations = recommendations[:limit]
    
    return recommendations


# ==================== LEGACY FUNCTIONS (Backward Compatibility) ====================

def get_ml_recommendations(user_id, method='hybrid'):
    """
    Legacy function - for backward compatibility
    Maps old method names to new strategy names
    """
    if method in ('hybrid', 'skill_only'):
        return get_recommendations(user_id, strategy='pure_skill')
    return []


def get_recommendation_methods():
    """Legacy function - for backward compatibility"""
    return get_recommendation_strategies()