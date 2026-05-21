# recommendation_engine.py
import mysql.connector
from db_config import get_db_connection

def get_job_recommendations(user_id, min_match_score=0):
    """
    Returns ranked job recommendations for a user
    """
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
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
        COALESCE(SUM(us.proficiency_level * js.importance_weight), 0) AS match_score
    FROM Jobs j
    JOIN Companies c ON j.company_id = c.company_id
    LEFT JOIN Job_Skills js ON j.job_id = js.job_id
    LEFT JOIN User_Skills us ON js.skill_id = us.skill_id AND us.user_id = %s
    GROUP BY j.job_id, j.title, j.description, j.min_experience, 
             j.salary_min, j.salary_max, c.company_name, c.location
    HAVING match_score >= %s
    ORDER BY match_score DESC
    """
    
    cursor.execute(query, (user_id, min_match_score))
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return results

def get_user_profile(user_id):
    """Get user details and skills"""
    conn = get_db_connection()
    if not conn:
        return {"user": None, "skills": []}
    
    cursor = conn.cursor(dictionary=True)
    
    # Get user basic info
    cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    
    # Get user skills
    cursor.execute("""
        SELECT s.skill_name, us.proficiency_level, us.years_experience
        FROM User_Skills us
        JOIN Skills s ON us.skill_id = s.skill_id
        WHERE us.user_id = %s
    """, (user_id,))
    skills = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {"user": user, "skills": skills}

def apply_for_job(user_id, job_id):
    """Submit job application"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    cursor = conn.cursor()
    
    try:
        # Check if already applied
        cursor.execute("""
            SELECT COUNT(*) FROM Applications 
            WHERE user_id = %s AND job_id = %s
        """, (user_id, job_id))
        count = cursor.fetchone()[0]
        
        if count > 0:
            return False, "You have already applied for this job."
        
        # Insert application
        cursor.execute("""
            INSERT INTO Applications (user_id, job_id, status, applied_date)
            VALUES (%s, %s, 'pending', CURDATE())
        """, (user_id, job_id))
        conn.commit()
        return True, "Application submitted successfully!"
        
    except mysql.connector.Error as err:
        return False, f"Database error: {err}"
    finally:
        cursor.close()
        conn.close()

def get_all_jobs():
    """Get all jobs for company view"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT j.*, c.company_name, c.location
        FROM Jobs j
        JOIN Companies c ON j.company_id = c.company_id
        ORDER BY j.job_id DESC
    """)
    jobs = cursor.fetchall()
    cursor.close()
    conn.close()
    return jobs

def get_job_details(job_id):
    """Get detailed job information"""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT j.*, c.company_name, c.location, c.industry
        FROM Jobs j
        JOIN Companies c ON j.company_id = c.company_id
        WHERE j.job_id = %s
    """, (job_id,))
    job = cursor.fetchone()
    cursor.close()
    conn.close()
    return job

def get_user_applications(user_id):
    """Get all applications for a user"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*, j.title, c.company_name
        FROM Applications a
        JOIN Jobs j ON a.job_id = j.job_id
        JOIN Companies c ON j.company_id = c.company_id
        WHERE a.user_id = %s
        ORDER BY a.applied_date DESC
    """, (user_id,))
    applications = cursor.fetchall()
    cursor.close()
    conn.close()
    return applications

def get_company_jobs(company_id):
    """Get all jobs for a company"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT j.*, 
               (SELECT COUNT(*) FROM Applications WHERE job_id = j.job_id) as applicant_count
        FROM Jobs j
        WHERE j.company_id = %s
        ORDER BY j.job_id DESC
    """, (company_id,))
    jobs = cursor.fetchall()
    cursor.close()
    conn.close()
    return jobs

def get_job_applicants(job_id):
    """Get all applicants for a specific job with match scores"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT
            u.user_id,
            u.name, 
            u.email, 
            u.degree, 
            u.cgpa, 
            u.graduation_year,
            a.status, 
            a.applied_date,
            COALESCE(
                (SELECT SUM(us2.proficiency_level * js2.importance_weight)
                 FROM User_Skills us2
                 JOIN Job_Skills js2 ON us2.skill_id = js2.skill_id
                 WHERE us2.user_id = u.user_id AND js2.job_id = %s
                ), 0
            ) as match_score
        FROM Applications a
        JOIN Users u ON a.user_id = u.user_id
        WHERE a.job_id = %s
        ORDER BY match_score DESC
    """, (job_id, job_id))
    applicants = cursor.fetchall()
    cursor.close()
    conn.close()
    return applicants

def update_application_status(application_id, status):
    """Update application status (for company use)"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Applications 
            SET status = %s 
            WHERE application_id = %s
        """, (status, application_id))
        conn.commit()
        return True
    except mysql.connector.Error:
        return False
    finally:
        cursor.close()
        conn.close()