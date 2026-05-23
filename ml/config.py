# ml/config.py
"""
ML Configuration Settings
"""

# Database settings
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'sem_proj'
}

# Predefined recommendation strategies
RECOMMENDATION_STRATEGIES = {
    'pure_skill': {
        'name': '🎯 Skill Based',
        'description': 'Based purely on your skills matching job requirements',
        'weights': {
            'skill_match': 1.0,
            'collaborative': 0.0,
            'popularity': 0.0
        }
    },
    'balanced': {
        'name': '⚖️ Balanced',
        'description': '50% Skills + 30% Similar Users + 20% Popular Jobs',
        'weights': {
            'skill_match': 0.5,
            'collaborative': 0.3,
            'popularity': 0.2
        }
    },
    'community': {
        'name': '👥 Social Recommendation',
        'description': 'Based on what similar students applied to',
        'weights': {
            'skill_match': 0.3,
            'collaborative': 0.6,
            'popularity': 0.1
        }
    },
    'trending': {
        'name': '🔥 Trending',
        'description': 'Popular jobs that many students are applying to',
        'weights': {
            'skill_match': 0.2,
            'collaborative': 0.2,
            'popularity': 0.6
        }
    }
}

# Model settings
MODEL_PATH = 'models/'
COLLAB_FILTERING_ENABLED = True
MAX_RECOMMENDATIONS = 20

# Skill matching settings
SKILL_MATCH_THRESHOLD = 0

# Collaborative filtering settings
MIN_COMMON_USERS = 2
SIMILARITY_METHOD = 'cosine'