# ml_integration.py
"""
Bridge between Flask app and ML components
"""

from ml.hybrid_recommender import HybridRecommender
from ml.config import RECOMMENDATION_STRATEGIES

# Global instance (load once)
_hybrid_recommender = None

def get_hybrid_recommender():
    """Get or create hybrid recommender instance"""
    global _hybrid_recommender
    if _hybrid_recommender is None:
        _hybrid_recommender = HybridRecommender()
        _hybrid_recommender.load_models()
    return _hybrid_recommender

def get_recommendations(user_id, strategy='pure_skill', limit=10):
    """
    Get ML-powered recommendations for a student
    
    Args:
        user_id: Student's user ID
        strategy: 'pure_skill', 'balanced', 'community', 'trending'
        limit: Max number of recommendations
    
    Returns:
        List of job recommendations
    """
    recommender = get_hybrid_recommender()
    recommendations = recommender.get_recommendations_by_strategy(user_id, strategy=strategy)
    
    # Apply limit
    if limit and len(recommendations) > limit:
        recommendations = recommendations[:limit]
    
    return recommendations

def get_recommendation_strategies():
    """Return available recommendation strategies"""
    return {
        'pure_skill': '🎯 Skill Based',
        'balanced': '⚖️ Balanced',
        'community': '👥 Social Recommendation',
        'trending': '🔥 Trending'
    }

def get_strategy_description(strategy):
    """Get description for a strategy"""
    descriptions = {
        'pure_skill': 'Based purely on your skills matching job requirements',
        'balanced': '50% Skills + 30% Similar Users + 20% Popular Jobs',
        'community': 'Based on what similar students applied to',
        'trending': 'Popular jobs that many students are applying to'
    }
    return descriptions.get(strategy, '')

def refresh_ml_models():
    """Force refresh of ML models"""
    global _hybrid_recommender
    _hybrid_recommender = None
    return {"status": "success", "message": "Models will reload on next request"}

# Keep legacy functions for compatibility
def get_ml_recommendations(user_id, method='hybrid'):
    """Legacy function - for backward compatibility"""
    if method == 'hybrid':
        return get_recommendations(user_id, strategy='pure_skill')
    elif method == 'skill_only':
        return get_recommendations(user_id, strategy='pure_skill')
    else:
        return []

def get_recommendation_methods():
    """Legacy function - for backward compatibility"""
    return get_recommendation_strategies()