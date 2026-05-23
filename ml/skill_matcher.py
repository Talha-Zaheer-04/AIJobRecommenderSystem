# ml/skill_matcher.py - USING EXACT DEBUG LOGIC
"""
Skill-based matching using direct database queries (same as debug script)
"""

import pandas as pd
from ml.data_preprocessor import DataPreprocessor

class SkillMatcher:
    def __init__(self):
        self.preprocessor = DataPreprocessor()
    
    def calculate_match_score(self, user_id, job_id):
        """Calculate match score using same logic as debug script"""
        conn = self.preprocessor.get_connection()
        if not conn:
            return 0
        
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
            return 0
        
        perfect_score = 0
        user_score = 0
        
        for skill in job_skills:
            skill_name = skill['skill_name']
            importance = skill['importance_weight']
            user_prof = user_skills.get(skill_name, 0)
            
            # Perfect user has proficiency 5 for all skills
            perfect_score += 5 * importance
            user_score += user_prof * importance
        
        if perfect_score > 0:
            percentage = (user_score / perfect_score) * 100
        else:
            percentage = 0
        
        return round(percentage, 1)
    
    def get_enhanced_recommendations(self, user_id, limit=20):
        """Get job recommendations for a user"""
        conn = self.preprocessor.get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        # Get all jobs
        cursor.execute("""
            SELECT DISTINCT j.job_id, j.title, j.description, j.min_experience, 
                   j.salary_min, j.salary_max, c.company_name, c.location
            FROM Jobs j
            JOIN Companies c ON j.company_id = c.company_id
        """)
        jobs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        results = []
        for job in jobs:
            score = self.calculate_match_score(user_id, job['job_id'])
            job['ml_match_score'] = score
            job['match_score'] = score
            results.append(job)
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Add required skills info
        for result in results[:limit]:
            result['required_skills'] = self._get_job_skills(result['job_id'])
        
        return results[:limit]
    
    def _get_job_skills(self, job_id):
        """Get required skills for a job"""
        conn = self.preprocessor.get_connection()
        if not conn:
            return ""
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.skill_name, js.importance_weight
            FROM Job_Skills js
            JOIN Skills s ON js.skill_id = s.skill_id
            WHERE js.job_id = %s
        """, (job_id,))
        skills = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return ', '.join([f"{s['skill_name']}({s['importance_weight']})" for s in skills])
    
    def calculate_match_scores(self, user_id):
        """Return DataFrame of match scores (for compatibility with hybrid recommender)"""
        recommendations = self.get_enhanced_recommendations(user_id, limit=50)
        
        if not recommendations:
            return pd.DataFrame()
        
        df = pd.DataFrame(recommendations)
        df = df[['job_id', 'ml_match_score']]
        return df
    
    def load_data(self):
        """Compatibility method"""
        return self