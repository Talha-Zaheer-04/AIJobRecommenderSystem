# ml/data_preprocessor.py
"""
Data extraction and preprocessing for ML models
"""

import mysql.connector
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from ml.config import DB_CONFIG

class DataPreprocessor:
    def __init__(self):
        self.conn = None
        self.user_encoder = LabelEncoder()
        self.job_encoder = LabelEncoder()
        self.scaler = MinMaxScaler()
    
    def get_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**DB_CONFIG)
    
    def load_user_skill_matrix(self):
        """
        Create user-skill matrix
        Returns: DataFrame with users as rows, skills as columns, proficiency as values
        """
        conn = self.get_connection()
        
        query = """
        SELECT 
            u.user_id,
            u.name,
            s.skill_id,
            s.skill_name,
            us.proficiency_level,
            us.years_experience
        FROM Users u
        JOIN User_Skills us ON u.user_id = us.user_id
        JOIN Skills s ON us.skill_id = s.skill_id
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Pivot to create user-skill matrix
        pivot_df = df.pivot_table(
            index='user_id', 
            columns='skill_name', 
            values='proficiency_level',
            fill_value=0
        )
        
        return pivot_df
    
    def load_job_skill_matrix(self):
        """
        Create job-skill matrix
        Returns: DataFrame with jobs as rows, skills as columns, importance as values
        """
        conn = self.get_connection()
        
        query = """
        SELECT 
            j.job_id,
            j.title,
            s.skill_id,
            s.skill_name,
            js.importance_weight
        FROM Jobs j
        JOIN Job_Skills js ON j.job_id = js.job_id
        JOIN Skills s ON js.skill_id = s.skill_id
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Pivot to create job-skill matrix
        pivot_df = df.pivot_table(
            index='job_id',
            columns='skill_name',
            values='importance_weight',
            fill_value=0
        )
        
        return pivot_df
    
    def load_user_applications(self):
        """
        Load user application history for collaborative filtering
        """
        conn = self.get_connection()
        
        query = """
        SELECT 
            a.user_id,
            a.job_id,
            a.status,
            a.applied_date,
            CASE 
                WHEN a.status = 'accepted' THEN 1
                WHEN a.status = 'pending' THEN 0.5
                ELSE 0
            END as rating
        FROM Applications a
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
    
    def load_all_jobs_with_skills(self):
        """
        Load all jobs with their required skills
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
            GROUP_CONCAT(DISTINCT s.skill_name) as required_skills
        FROM Jobs j
        JOIN Companies c ON j.company_id = c.company_id
        LEFT JOIN Job_Skills js ON j.job_id = js.job_id
        LEFT JOIN Skills s ON js.skill_id = s.skill_id
        GROUP BY j.job_id
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
    
    def load_user_profile_complete(self, user_id):
        """
        Load complete user profile for personalized recommendations
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
        SELECT j.job_id, j.title, a.status
        FROM Applications a
        JOIN Jobs j ON a.job_id = j.job_id
        WHERE a.user_id = %s
        """
        apps_df = pd.read_sql(apps_query, conn, params=[user_id])
        
        conn.close()
        
        return {
            'user_info': user_df,
            'skills': skills_df,
            'applications': apps_df
        }
    
    def get_user_vector(self, user_id, skill_matrix):
        """
        Get user skill vector as numpy array
        """
        if user_id in skill_matrix.index:
            return skill_matrix.loc[user_id].values
        return np.zeros(len(skill_matrix.columns))