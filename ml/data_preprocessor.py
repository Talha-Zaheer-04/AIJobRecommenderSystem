# ml/data_preprocessor.py
"""
Data extraction and preprocessing for ML models
Handles loading and transforming data from database to ML-ready formats
"""

import warnings
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from ml.config import DB_CONFIG

# Suppress pandas warning about SQL injection (we trust our queries)
warnings.filterwarnings('ignore', category=UserWarning)


class DataPreprocessor:
    """
    Handles all data extraction and preprocessing for ML models
    Loads user skills, job requirements, and application history from database
    """
    
    def __init__(self):
        """Initialize preprocessor with encoders and scalers"""
        self.user_encoder = LabelEncoder()
        self.job_encoder = LabelEncoder()
        self.scaler = MinMaxScaler()
    
    # ==================== CONNECTION MANAGEMENT ====================
    
    def get_connection(self):
        """Get database connection using configuration"""
        import mysql.connector
        return mysql.connector.connect(**DB_CONFIG)
    
    # ==================== SKILL MATRICES ====================
    
    def load_user_skill_matrix(self) -> pd.DataFrame:
        """
        Create user-skill matrix
        Returns DataFrame with users as rows, skills as columns, proficiency as values
        
        Example:
            user_id | Python | SQL | Java
            1       | 5      | 4   | 0
            2       | 3      | 0   | 5
        """
        conn = self.get_connection()
        
        query = """
            SELECT 
                u.user_id,
                u.name,
                s.skill_name,
                us.proficiency_level
            FROM Users u
            JOIN User_Skills us ON u.user_id = us.user_id
            JOIN Skills s ON us.skill_id = s.skill_id
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
        
        # Pivot to create user-skill matrix
        pivot_df = df.pivot_table(
            index='user_id',
            columns='skill_name',
            values='proficiency_level',
            fill_value=0
        )
        
        return pivot_df
    
    def load_job_skill_matrix(self) -> pd.DataFrame:
        """
        Create job-skill matrix
        Returns DataFrame with jobs as rows, skills as columns, importance as values
        
        Example:
            job_id | Python | SQL | Java
            1      | 5      | 3   | 0
            2      | 0      | 5   | 4
        """
        conn = self.get_connection()
        
        query = """
            SELECT 
                j.job_id,
                j.title,
                s.skill_name,
                js.importance_weight
            FROM Jobs j
            JOIN Job_Skills js ON j.job_id = js.job_id
            JOIN Skills s ON js.skill_id = s.skill_id
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
        
        # Pivot to create job-skill matrix
        pivot_df = df.pivot_table(
            index='job_id',
            columns='skill_name',
            values='importance_weight',
            fill_value=0
        )
        
        return pivot_df
    
    # ==================== APPLICATION DATA ====================
    
    def load_user_applications(self) -> pd.DataFrame:
        """
        Load user application history for collaborative filtering
        Converts status to numerical ratings:
        - accepted: 1.0
        - pending: 0.5
        - rejected/cancelled: 0.0
        """
        conn = self.get_connection()
        
        query = """
            SELECT 
                a.user_id,
                a.job_id,
                a.status,
                a.applied_date,
                CASE 
                    WHEN a.status = 'accepted' THEN 1.0
                    WHEN a.status = 'pending' THEN 0.5
                    ELSE 0.0
                END as rating
            FROM Applications a
            WHERE a.status != 'cancelled'
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
    
    # ==================== JOB DETAILS ====================
    
    def load_all_jobs_with_skills(self) -> pd.DataFrame:
        """
        Load all jobs with their required skills as comma-separated string
        Returns DataFrame with job details and required_skills column
        """
        conn = self.get_connection()
        
        query = """
            SELECT 
                j.job_id,
                j.title,
                j.description,
                j.min_experience,
                j.salary_min,
                j.salary_max,
                c.company_name,
                c.location,
                GROUP_CONCAT(DISTINCT s.skill_name ORDER BY s.skill_name) as required_skills
            FROM Jobs j
            JOIN Companies c ON j.company_id = c.company_id
            LEFT JOIN Job_Skills js ON j.job_id = js.job_id
            LEFT JOIN Skills s ON js.skill_id = s.skill_id
            GROUP BY j.job_id
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Replace NULL with empty string
        df['required_skills'] = df['required_skills'].fillna('')
        
        return df
    
    # ==================== USER PROFILES ====================
    
    def load_user_profile_complete(self, user_id: int) -> dict:
        """
        Load complete user profile for personalized recommendations
        
        Args:
            user_id: Student's user ID
        
        Returns:
            Dictionary with 'user_info', 'skills', and 'applications' DataFrames
        """
        conn = self.get_connection()
        
        # Get user details
        user_query = "SELECT * FROM Users WHERE user_id = %s"
        user_df = pd.read_sql(user_query, conn, params=[user_id])
        
        # Get user skills
        skills_query = """
            SELECT s.skill_name, us.proficiency_level, us.years_experience
            FROM User_Skills us
            JOIN Skills s ON us.skill_id = s.skill_id
            WHERE us.user_id = %s
        """
        skills_df = pd.read_sql(skills_query, conn, params=[user_id])
        
        # Get user applications
        apps_query = """
            SELECT j.job_id, j.title, a.status, a.applied_date
            FROM Applications a
            JOIN Jobs j ON a.job_id = j.job_id
            WHERE a.user_id = %s
            ORDER BY a.applied_date DESC
        """
        apps_df = pd.read_sql(apps_query, conn, params=[user_id])
        
        conn.close()
        
        return {
            'user_info': user_df,
            'skills': skills_df,
            'applications': apps_df
        }
    
    # ==================== VECTOR UTILITIES ====================
    
    def get_user_vector(self, user_id: int, skill_matrix: pd.DataFrame) -> np.ndarray:
        """
        Get user skill vector as numpy array
        
        Args:
            user_id: Student's user ID
            skill_matrix: DataFrame from load_user_skill_matrix()
        
        Returns:
            Numpy array of skill proficiencies (zeros if user not found)
        """
        if user_id in skill_matrix.index:
            return skill_matrix.loc[user_id].values
        return np.zeros(len(skill_matrix.columns))
    
    def get_job_vector(self, job_id: int, skill_matrix: pd.DataFrame) -> np.ndarray:
        """
        Get job skill vector as numpy array
        
        Args:
            job_id: Job ID
            skill_matrix: DataFrame from load_job_skill_matrix()
        
        Returns:
            Numpy array of skill importances (zeros if job not found)
        """
        if job_id in skill_matrix.index:
            return skill_matrix.loc[job_id].values
        return np.zeros(len(skill_matrix.columns))