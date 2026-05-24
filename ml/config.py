# ml/config.py
"""
ML Configuration Settings for Job Recommendation System
Contains all configurable parameters for ML models and recommendation strategies
"""

# ==================== DATABASE SETTINGS ====================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'sem_proj'
}


# ==================== RECOMMENDATION STRATEGIES ====================
# Each strategy has:
#   - name: Display name for UI
#   - description: Human-readable explanation
#   - weights: Contribution of each factor (must sum to 1.0)

RECOMMENDATION_STRATEGIES = {
    'pure_skill': {
        'name': '🎯 Skill Based',
        'description': 'Based purely on your skills matching job requirements',
        'weights': {
            'skill_match': 1.0,      # 100% skill matching
            'collaborative': 0.0,    # 0% collaborative filtering
            'popularity': 0.0        # 0% popularity
        }
    },
    'balanced': {
        'name': '⚖️ Balanced',
        'description': '50% Skills + 30% Similar Users + 20% Popular Jobs',
        'weights': {
            'skill_match': 0.5,      # 50% skill matching
            'collaborative': 0.3,    # 30% collaborative filtering
            'popularity': 0.2        # 20% popularity
        }
    },
    'community': {
        'name': '👥 Social Recommendation',
        'description': 'Based on what similar students applied to',
        'weights': {
            'skill_match': 0.3,      # 30% skill matching
            'collaborative': 0.6,    # 60% collaborative filtering
            'popularity': 0.1        # 10% popularity
        }
    },
    'trending': {
        'name': '🔥 Trending',
        'description': 'Popular jobs that many students are applying to',
        'weights': {
            'skill_match': 0.2,      # 20% skill matching
            'collaborative': 0.2,    # 20% collaborative filtering
            'popularity': 0.6        # 60% popularity
        }
    }
}


# ==================== MODEL SETTINGS ====================

MODEL_PATH = 'models/'                    # Directory for saved models
COLLAB_FILTERING_ENABLED = True           # Enable/disable collaborative filtering
MAX_RECOMMENDATIONS = 20                  # Maximum number of recommendations to return


# ==================== SKILL MATCHING SETTINGS ====================

SKILL_MATCH_THRESHOLD = 0                 # Minimum match score to consider (0-100)


# ==================== COLLABORATIVE FILTERING SETTINGS ====================

MIN_COMMON_USERS = 2                      # Minimum users in common for similarity
SIMILARITY_METHOD = 'cosine'              # Similarity method: 'cosine' or 'pearson'


# ==================== HELPER FUNCTIONS ====================

def get_strategy_names():
    """Get list of all strategy names"""
    return list(RECOMMENDATION_STRATEGIES.keys())


def get_strategy_weights(strategy_name):
    """Get weights for a specific strategy"""
    return RECOMMENDATION_STRATEGIES.get(strategy_name, {}).get('weights', None)


def validate_weights():
    """Validate that all strategy weights sum to 1.0"""
    for name, strategy in RECOMMENDATION_STRATEGIES.items():
        weights = strategy['weights']
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:  # Allow small floating point error
            print(f"Warning: Strategy '{name}' weights sum to {total}, should be 1.0")


def get_db_connection_config():
    """Get database connection configuration (without exposing password in logs)"""
    return {
        'host': DB_CONFIG['host'],
        'user': DB_CONFIG['user'],
        'database': DB_CONFIG['database']
    }


# ==================== VALIDATE ON IMPORT ====================

validate_weights()