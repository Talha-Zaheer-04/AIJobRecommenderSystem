# ml/config.py
"""
ML Configuration Settings
"""

# Database settings (reuse existing)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'sem_proj'
}

# Model settings
MODEL_PATH = 'models/'
COLLAB_FILTERING_ENABLED = True
HYBRID_WEIGHTS = {
    'skill_match': 0.6,      # 60% weight to skill matching
    'collaborative': 0.3,    # 30% weight to collaborative filtering
    'popularity': 0.1        # 10% weight to popularity
}

# Skill matching settings
SKILL_MATCH_THRESHOLD = 10   # Minimum match score to consider
MAX_RECOMMENDATIONS = 20     # Max jobs to recommend

# Collaborative filtering settings
MIN_COMMON_USERS = 2         # Minimum users in common for similarity
SIMILARITY_METHOD = 'cosine'  # 'cosine' or 'pearson'