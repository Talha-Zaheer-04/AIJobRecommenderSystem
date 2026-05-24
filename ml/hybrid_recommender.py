# ml/hybrid_recommender.py
"""
Hybrid Recommender with multiple recommendation strategies
Combines skill-based, collaborative filtering, and popularity scores
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from ml.skill_matcher import SkillMatcher
from ml.collaborative_filter import CollaborativeFilter
from ml.config import RECOMMENDATION_STRATEGIES, MAX_RECOMMENDATIONS


class HybridRecommender:
    """
    Hybrid recommender that combines multiple recommendation strategies
    Supports pure_skill, balanced, community, and trending strategies
    """
    
    def __init__(self):
        """Initialize with skill matcher and collaborative filter"""
        self.skill_matcher = SkillMatcher()
        self.collaborative_filter = CollaborativeFilter()
        self.is_loaded = False
    
    # ==================== MODEL MANAGEMENT ====================
    
    def load_models(self):
        """Load all required models and data"""
        self.skill_matcher.load_data()
        self.collaborative_filter.build_user_job_matrix()
        self.collaborative_filter.calculate_user_similarity()
        self.is_loaded = True
        return self
    
    # ==================== CORE RECOMMENDATION ENGINE ====================
    
    def get_recommendations_by_strategy(self, user_id: int, strategy: str = 'pure_skill') -> List[Dict[str, Any]]:
        """
        Get recommendations based on selected strategy
        
        Strategies:
            - pure_skill: 100% skill matching
            - balanced: 50% skill, 30% collaborative, 20% popularity
            - community: 30% skill, 60% collaborative, 10% popularity
            - trending: 20% skill, 20% collaborative, 60% popularity
        
        Args:
            user_id: Student's user ID
            strategy: One of 'pure_skill', 'balanced', 'community', 'trending'
        
        Returns:
            List of job dictionaries with match_score and recommendation_type
        """
        if not self.is_loaded:
            self.load_models()
        
        # Get strategy weights
        strategy_config = RECOMMENDATION_STRATEGIES.get(strategy, RECOMMENDATION_STRATEGIES['pure_skill'])
        weights = strategy_config['weights']
        
        # Get skill-based recommendations
        skill_recommendations = self.skill_matcher.get_enhanced_recommendations(user_id, limit=MAX_RECOMMENDATIONS)
        
        if not skill_recommendations:
            return []
        
        # Create DataFrame from skill recommendations
        skill_df = pd.DataFrame(skill_recommendations)
        skill_df = skill_df.rename(columns={'ml_match_score': 'skill_score'})
        skill_df['skill_score'] = skill_df['skill_score'].fillna(0)
        
        # Get collaborative filtering results
        collab_results = self.collaborative_filter.get_collaborative_recommendations(user_id)
        collab_df = pd.DataFrame(collab_results) if collab_results else pd.DataFrame()
        if not collab_df.empty:
            collab_df = collab_df.rename(columns={'collab_score': 'collab_score'})
        
        # Get popularity scores
        popularity_scores = self._get_popularity_scores()
        
        # Get all jobs for details
        all_jobs = self.skill_matcher.preprocessor.load_all_jobs_with_skills()
        
        # Build final scores
        final_scores = self._combine_scores(
            skill_df, collab_df, popularity_scores, weights
        )
        
        if final_scores.empty:
            return []
        
        # Merge with job details and format output
        results = all_jobs.merge(final_scores, on='job_id')
        results['match_score'] = results['final_score'].round(1)
        results['recommendation_type'] = strategy_config['name']
        
        return self._format_output(results)
    
    # ==================== SCORING METHODS ====================
    
    def _combine_scores(self, skill_df: pd.DataFrame, collab_df: pd.DataFrame, 
                        popularity_df: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
        """
        Combine skill, collaborative, and popularity scores with given weights
        
        Args:
            skill_df: DataFrame with skill_score for each job
            collab_df: DataFrame with collab_score for each job
            popularity_df: DataFrame with popularity_score for each job
            weights: Dictionary with skill_match, collaborative, popularity weights
        
        Returns:
            DataFrame with final_score for each job
        """
        # Start with skill scores
        final_scores = skill_df[['job_id', 'skill_score']].copy()
        final_scores['collab_score'] = 0
        final_scores['popularity_score'] = 0
        final_scores['final_score'] = final_scores['skill_score'] * weights['skill_match']
        
        # Add collaborative scores
        if not collab_df.empty:
            final_scores = self._add_collaborative_scores(final_scores, collab_df, weights['collaborative'])
        
        # Add popularity scores
        if not popularity_df.empty:
            final_scores = self._add_popularity_scores(final_scores, popularity_df, weights['popularity'])
        
        # Sort by final score
        final_scores = final_scores.sort_values('final_score', ascending=False)
        final_scores = final_scores.head(MAX_RECOMMENDATIONS)
        
        return final_scores
    
    def _add_collaborative_scores(self, final_scores: pd.DataFrame, 
                                   collab_df: pd.DataFrame, weight: float) -> pd.DataFrame:
        """Add collaborative filtering scores to final scores"""
        for _, row in collab_df.iterrows():
            job_id = row['job_id']
            collab_score = row.get('collab_score', 0)
            
            if job_id in final_scores['job_id'].values:
                idx = final_scores[final_scores['job_id'] == job_id].index[0]
                final_scores.loc[idx, 'collab_score'] = collab_score
                final_scores.loc[idx, 'final_score'] += collab_score * weight
            else:
                # Add new job from collaborative results
                new_row = pd.DataFrame([{
                    'job_id': job_id,
                    'skill_score': 0,
                    'collab_score': collab_score,
                    'popularity_score': 0,
                    'final_score': collab_score * weight
                }])
                final_scores = pd.concat([final_scores, new_row], ignore_index=True)
        
        return final_scores
    
    def _add_popularity_scores(self, final_scores: pd.DataFrame, 
                                popularity_df: pd.DataFrame, weight: float) -> pd.DataFrame:
        """Add popularity scores to final scores"""
        for _, row in popularity_df.iterrows():
            job_id = row['job_id']
            popularity_score = row['popularity_score']
            
            if job_id in final_scores['job_id'].values:
                idx = final_scores[final_scores['job_id'] == job_id].index[0]
                final_scores.loc[idx, 'popularity_score'] = popularity_score
                final_scores.loc[idx, 'final_score'] += popularity_score * weight
        
        return final_scores
    
    def _get_popularity_scores(self) -> pd.DataFrame:
        """
        Calculate popularity score for each job based on application count
        Score ranges from 0-100, where most popular job gets 100
        """
        conn = self.skill_matcher.preprocessor.get_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            # Get max application count for normalization
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM Applications 
                WHERE status != 'cancelled'
                GROUP BY job_id 
                ORDER BY cnt DESC 
                LIMIT 1
            """)
            max_result = cursor.fetchone()
            max_count = max_result[0] if max_result else 1
            cursor.close()
            
            # Calculate popularity scores (0-100 scale)
            query = """
                SELECT 
                    j.job_id,
                    COUNT(a.application_id) as application_count,
                    (COUNT(a.application_id) * 1.0 / %s) * 100 as popularity_score
                FROM Jobs j
                LEFT JOIN Applications a ON j.job_id = a.job_id AND a.status != 'cancelled'
                GROUP BY j.job_id
            """
            
            df = pd.read_sql(query, conn, params=[max_count])
            conn.close()
            
            df['popularity_score'] = df['popularity_score'].fillna(0)
            
        except Exception as e:
            print(f"Error calculating popularity scores: {e}")
            conn.close()
            return pd.DataFrame()
        
        return df[['job_id', 'popularity_score']]
    
    # ==================== OUTPUT FORMATTING ====================
    
    def _format_output(self, results: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Format DataFrame results to list of dictionaries for template
        
        Args:
            results: DataFrame with job recommendations
        
        Returns:
            List of dictionaries with clean field names
        """
        output = []
        for _, row in results.iterrows():
            output.append({
                'job_id': row['job_id'],
                'title': row['title'],
                'company_name': row['company_name'],
                'location': row['location'],
                'description': row['description'],
                'min_experience': row['min_experience'],
                'salary_min': row['salary_min'],
                'salary_max': row['salary_max'],
                'required_skills': row.get('required_skills', ''),
                'match_score': row['match_score'],
                'ml_match_score': row['skill_score'],
                'recommendation_type': row['recommendation_type']
            })
        
        return output
    
    # ==================== LEGACY METHODS ====================
    
    def get_hybrid_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Legacy method - defaults to pure_skill strategy
        
        Args:
            user_id: Student's user ID
        
        Returns:
            List of job recommendations
        """
        return self.get_recommendations_by_strategy(user_id, 'pure_skill')