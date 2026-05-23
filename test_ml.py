# test_ml.py
"""
Test ML recommendation system
"""

from ml_integration import get_ml_recommendations, get_skill_matcher, get_hybrid_recommender

def test_skill_matcher():
    print("=" * 50)
    print("Testing Skill Matcher for user_id=1")
    print("=" * 50)
    
    matcher = get_skill_matcher()
    recs = matcher.get_enhanced_recommendations(1, limit=5)
    
    for rec in recs:
        print(f"- {rec['title']} at {rec['company_name']}: Match Score {rec.get('ml_match_score', 0):.2f}")

def test_hybrid_recommender():
    print("\n" + "=" * 50)
    print("Testing Hybrid Recommender for user_id=1")
    print("=" * 50)
    
    recommender = get_hybrid_recommender()
    recs = recommender.get_hybrid_recommendations(1)
    
    for rec in recs[:5]:
        print(f"- {rec['title']} at {rec['company_name']}: Final Score {rec.get('match_score', 0):.2f}")

if __name__ == "__main__":
    test_skill_matcher()
    test_hybrid_recommender()