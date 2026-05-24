# ml/skill_matcher.py
"""
Skill-based matching using direct database queries
Calculates match scores based on user proficiency vs job requirements
"""

import pandas as pd
from typing import List, Dict, Any
from ml.data_preprocessor import DataPreprocessor


class SkillMatcher:
    """
    Calculates skill match scores between users and jobs
    Uses per-job perfect score normalization (0-100%)
    """
    
    def __init__(self):
        """Initialize with data preprocessor"""
        self.preprocessor = DataPreprocessor()
    
    # ==================== CORE MATCHING LOGIC ====================
    
    def calculate_match_score(self, user_id: int, job_id: int) -> float:
        """
        Calculate match score for a single user and job
        
        Formula: (sum(user_proficiency × importance) / (5 × sum(importance))) × 100
        
        Args:
            user_id: Student's user ID
            job_id: Job ID
        
        Returns:
            Match percentage (0-100), rounded to 1 decimal
        """
        conn = self.preprocessor.get_connection()
        if not conn:
            return 0.0
        
        cursor = conn.cursor(dictionary=True)
        
        # Get user's skills
        cursor.execute("""
            SELECT s.skill_name, us.proficiency_level
            FROM User_Skills us
            JOIN Skills s ON us.skill_id = s.skill_id
            WHERE us.user_id = %s
        """, (user_id,))
        user_skills = {row['skill_name']: row['proficiency_level'] for row in cursor.fetchall()}
        
        # Get job's required skills
        cursor.execute("""
            SELECT s.skill_name, js.importance_weight
            FROM Job_Skills js
            JOIN Skills s ON js.skill_id = s.skill_id
            WHERE js.job_id = %s
        """, (job_id,))
        job_skills = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not job_skills:
            return 0.0
        
        perfect_score = 0.0
        user_score = 0.0
        
        for skill in job_skills:
            skill_name = skill['skill_name']
            importance = skill['importance_weight']
            user_prof = user_skills.get(skill_name, 0)
            
            # Perfect user has proficiency 5 for all required skills
            perfect_score += 5.0 * importance
            user_score += user_prof * importance
        
        if perfect_score > 0:
            percentage = (user_score / perfect_score) * 100
        else:
            percentage = 0.0
        
        return round(percentage, 1)
    
    # ==================== RECOMMENDATION ENGINE ====================
    
    def get_enhanced_recommendations(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get job recommendations for a user sorted by match score
        
        Args:
            user_id: Student's user ID
            limit: Maximum number of recommendations to return
        
        Returns:
            List of job dictionaries with match_score and required_skills
        """
        conn = self.preprocessor.get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        # Get all jobs
        cursor.execute("""
            SELECT DISTINCT 
                j.job_id, 
                j.title, 
                j.description, 
                j.min_experience, 
                j.salary_min, 
                j.salary_max, 
                c.company_name, 
                c.location
            FROM Jobs j
            JOIN Companies c ON j.company_id = c.company_id
        """)
        jobs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Calculate scores for each job
        results = []
        for job in jobs:
            score = self.calculate_match_score(user_id, job['job_id'])
            job['ml_match_score'] = score
            job['match_score'] = score
            results.append(job)
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Add required skills info for top results
        for result in results[:limit]:
            result['required_skills'] = self._get_job_skills(result['job_id'])
        
        return results[:limit]
    
    # ==================== SKILLS UTILITIES ====================
    
    def _get_job_skills(self, job_id: int) -> str:
        """
        Get required skills for a job as formatted string
        
        Args:
            job_id: Job ID
        
        Returns:
            Comma-separated string like "Python(5), SQL(3)"
        """
        conn = self.preprocessor.get_connection()
        if not conn:
            return ""
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.skill_name, js.importance_weight
            FROM Job_Skills js
            JOIN Skills s ON js.skill_id = s.skill_id
            WHERE js.job_id = %s
            ORDER BY js.importance_weight DESC
        """, (job_id,))
        skills = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return ', '.join([f"{s['skill_name']}({s['importance_weight']})" for s in skills])
    
    # ==================== COMPATIBILITY METHODS ====================
    
    def calculate_match_scores(self, user_id: int) -> pd.DataFrame:
        """
        Return DataFrame of match scores for compatibility with hybrid recommender
        
        Args:
            user_id: Student's user ID
        
        Returns:
            DataFrame with columns 'job_id' and 'ml_match_score'
        """
        recommendations = self.get_enhanced_recommendations(user_id, limit=50)
        
        if not recommendations:
            return pd.DataFrame()
        
        df = pd.DataFrame(recommendations)
        return df[['job_id', 'ml_match_score']]
    
    def load_data(self):
        """Compatibility method for hybrid recommender"""
        return self