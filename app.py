# app.py - Cleaned and Optimized Version
"""
AI Job Recommendation System - Main Flask Application
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_config import get_db_connection
from recommendation_engine import get_user_profile, apply_for_job
from ml_integration import get_recommendations, get_recommendation_strategies, get_strategy_description
import mysql.connector

app = Flask(__name__)
app.secret_key = '123'


# ==================== HELPER FUNCTIONS ====================

def get_applications_count(user_id):
    """Get total applications count for a student"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as total FROM Applications WHERE user_id = %s", (user_id,))
    count = cursor.fetchone()['total']
    cursor.close()
    conn.close()
    return count


# ==================== ML INTEGRATION ROUTES ====================

@app.route('/recommendations')
def recommendations():
    """Get ML-powered job recommendations"""
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    min_score = request.args.get('min_score', 0, type=int)
    strategy = request.args.get('strategy', 'pure_skill')
    limit = request.args.get('limit', 10, type=int)
    
    ml_recs = get_recommendations(session['user_id'], strategy=strategy, limit=limit)
    
    if min_score > 0:
        ml_recs = [r for r in ml_recs if r.get('match_score', 0) >= min_score]
    
    strategies = get_recommendation_strategies()
    
    return render_template('recommendations.html',
                         recommendations=ml_recs,
                         min_score=min_score,
                         current_strategy=strategy,
                         current_strategy_name=strategies.get(strategy, 'Skill Based'),
                         strategy_description=get_strategy_description(strategy),
                         strategies=strategies,
                         limit=limit)


# ==================== PUBLIC ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if user_type == 'student':
            cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user and user['password'] == password:
                session.update({
                    'user_id': user['user_id'],
                    'user_name': user['name'],
                    'user_email': user['email'],
                    'user_type': 'student'
                })
                cursor.close()
                conn.close()
                return redirect(url_for('dashboard'))
        
        elif user_type == 'company':
            cursor.execute("SELECT * FROM Companies WHERE email = %s", (email,))
            company = cursor.fetchone()
            if company and company['password'] == password:
                session.update({
                    'company_id': company['company_id'],
                    'company_name': company['company_name'],
                    'company_email': company['email'],
                    'user_type': 'company'
                })
                cursor.close()
                conn.close()
                return redirect(url_for('company_jobs'))
        
        cursor.close()
        conn.close()
        flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ==================== SIGN UP ROUTES ====================

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup/student', methods=['GET', 'POST'])
def signup_student():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if not all([name, email, password]):
            flash('Name, email and password are required!', 'error')
            return redirect(url_for('signup_student'))
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('signup_student'))
        
        if len(password) < 4:
            flash('Password must be at least 4 characters long!', 'error')
            return redirect(url_for('signup_student'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO Users (name, email, password, degree, cgpa, graduation_year)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, email, password,
                  request.form.get('degree', ''),
                  request.form.get('cgpa'),
                  request.form.get('graduation_year')))
            conn.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Email already exists!', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('signup_student.html')

@app.route('/signup/company', methods=['GET', 'POST'])
def signup_company():
    if request.method == 'POST':
        company_name = request.form['company_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if not all([company_name, email, password]):
            flash('Company name, email and password are required!', 'error')
            return redirect(url_for('signup_company'))
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('signup_company'))
        
        if len(password) < 4:
            flash('Password must be at least 4 characters long!', 'error')
            return redirect(url_for('signup_company'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO Companies (company_name, email, password, industry, location)
                VALUES (%s, %s, %s, %s, %s)
            """, (company_name, email, password,
                  request.form.get('industry', ''),
                  request.form.get('location', '')))
            conn.commit()
            flash('Company account created successfully!', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Email already exists!', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('signup_company.html')


# ==================== STUDENT ROUTES ====================

@app.route('/dashboard')
def dashboard():
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    profile = get_user_profile(session['user_id'])
    if not profile['user']:
        flash('Profile not found', 'error')
        return redirect(url_for('logout'))
    
    profile['applications_count'] = get_applications_count(session['user_id'])
    return render_template('dashboard.html', profile=profile)

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply_to_job(job_id):
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        success, message = apply_for_job(session['user_id'], job_id)
        flash(message, 'success' if success else 'error')
        return redirect(url_for('applications'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT j.*, c.company_name, c.location,
               COALESCE(
                   (SELECT SUM(us.proficiency_level * js.importance_weight)
                    FROM User_Skills us
                    JOIN Job_Skills js ON us.skill_id = js.skill_id
                    WHERE us.user_id = %s AND js.job_id = j.job_id
                   ), 0
               ) as match_score
        FROM Jobs j
        JOIN Companies c ON j.company_id = c.company_id
        WHERE j.job_id = %s
    """, (session['user_id'], job_id))
    job = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('apply.html', job=job)

@app.route('/applications')
def applications():
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*, j.title, c.company_name, a.status
        FROM Applications a
        JOIN Jobs j ON a.job_id = j.job_id
        JOIN Companies c ON j.company_id = c.company_id
        WHERE a.user_id = %s
        ORDER BY a.applied_date DESC
    """, (session['user_id'],))
    applications = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('applications.html', applications=applications)


# ==================== CANCEL APPLICATION ====================

@app.route('/cancel_application/<int:application_id>', methods=['POST'])
def cancel_application(application_id):
    """Student cancels/withdraws their job application"""
    if session.get('user_type') != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM Applications 
        WHERE application_id = %s AND user_id = %s
    """, (application_id, session['user_id']))
    application = cursor.fetchone()
    
    if not application:
        flash('Application not found', 'error')
        return redirect(url_for('applications'))
    
    if application['status'] != 'pending':
        flash('You can only cancel pending applications!', 'error')
        return redirect(url_for('applications'))
    
    cursor.execute("""
        UPDATE Applications SET status = 'cancelled' WHERE application_id = %s
    """, (application_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Application cancelled successfully!', 'success')
    return redirect(url_for('applications'))


# ==================== STUDENT PROFILE EDITING ====================

@app.route('/student/edit_profile', methods=['GET', 'POST'])
def edit_student_profile():
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        
        if not name or not email:
            flash('Name and email are required!', 'error')
            return redirect(url_for('edit_student_profile'))
        
        try:
            cursor.execute("""
                UPDATE Users 
                SET name = %s, email = %s, degree = %s, cgpa = %s, graduation_year = %s
                WHERE user_id = %s
            """, (name, email,
                  request.form.get('degree', ''),
                  request.form.get('cgpa'),
                  request.form.get('graduation_year'),
                  session['user_id']))
            conn.commit()
            session.update({'user_name': name, 'user_email': email})
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        except mysql.connector.IntegrityError:
            flash('Email already exists!', 'error')
        finally:
            cursor.close()
            conn.close()
    
    cursor.execute("SELECT * FROM Users WHERE user_id = %s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('edit_student_profile.html', user=user)

@app.route('/student/change_password', methods=['GET', 'POST'])
def change_student_password():
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        current = request.form['current_password']
        new_pass = request.form['new_password']
        confirm = request.form['confirm_password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT password FROM Users WHERE user_id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        if user['password'] != current:
            flash('Current password is incorrect!', 'error')
        elif new_pass != confirm:
            flash('New passwords do not match!', 'error')
        elif len(new_pass) < 4:
            flash('Password must be at least 4 characters long!', 'error')
        else:
            cursor.execute("UPDATE Users SET password = %s WHERE user_id = %s", (new_pass, session['user_id']))
            conn.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        cursor.close()
        conn.close()
    
    return render_template('change_password.html', user_type='student')


# ==================== COMPANY ROUTES ====================

@app.route('/company/change_password', methods=['GET', 'POST'])
def change_company_password():
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        current = request.form['current_password']
        new_pass = request.form['new_password']
        confirm = request.form['confirm_password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT password FROM Companies WHERE company_id = %s", (session['company_id'],))
        company = cursor.fetchone()
        
        if company['password'] != current:
            flash('Current password is incorrect!', 'error')
        elif new_pass != confirm:
            flash('New passwords do not match!', 'error')
        elif len(new_pass) < 4:
            flash('Password must be at least 4 characters long!', 'error')
        else:
            cursor.execute("UPDATE Companies SET password = %s WHERE company_id = %s", (new_pass, session['company_id']))
            conn.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('company_profile'))
        
        cursor.close()
        conn.close()
    
    return render_template('change_password.html', user_type='company')

@app.route('/company/profile')
def company_profile():
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Companies WHERE company_id = %s", (session['company_id'],))
    company = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) as total FROM Jobs WHERE company_id = %s", (session['company_id'],))
    jobs_count = cursor.fetchone()['total']
    
    cursor.execute("""
        SELECT COUNT(*) as total FROM Applications a
        JOIN Jobs j ON a.job_id = j.job_id
        WHERE j.company_id = %s
    """, (session['company_id'],))
    applications_count = cursor.fetchone()['total']
    
    cursor.close()
    conn.close()
    
    return render_template('company_profile.html',
                         company=company,
                         jobs_count=jobs_count,
                         applications_count=applications_count)

@app.route('/company_jobs')
def company_jobs():
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Companies WHERE company_id = %s", (session['company_id'],))
    company = cursor.fetchone()
    
    cursor.execute("""
        SELECT j.*, 
               (SELECT COUNT(*) FROM Applications WHERE job_id = j.job_id AND status != 'cancelled') as applicant_count
        FROM Jobs j
        WHERE j.company_id = %s
        ORDER BY j.job_id DESC
    """, (session['company_id'],))
    jobs = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) as total FROM Jobs WHERE company_id = %s", (session['company_id'],))
    jobs_count = cursor.fetchone()['total']
    
    cursor.execute("""
        SELECT COUNT(*) as total FROM Applications a
        JOIN Jobs j ON a.job_id = j.job_id
        WHERE j.company_id = %s AND a.status != 'cancelled'
    """, (session['company_id'],))
    applications_count = cursor.fetchone()['total']
    
    cursor.close()
    conn.close()
    
    return render_template('company_jobs.html',
                         jobs=jobs,
                         jobs_count=jobs_count,
                         applications_count=applications_count,
                         company=company)

@app.route('/company/edit_profile', methods=['GET', 'POST'])
def edit_company_profile():
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        cursor.execute("""
            UPDATE Companies 
            SET company_name = %s, industry = %s, location = %s, email = %s
            WHERE company_id = %s
        """, (request.form['company_name'],
              request.form['industry'],
              request.form['location'],
              request.form['email'],
              session['company_id']))
        conn.commit()
        session.update({
            'company_name': request.form['company_name'],
            'company_email': request.form['email']
        })
        cursor.close()
        conn.close()
        flash('Company profile updated successfully!', 'success')
        return redirect(url_for('company_profile'))
    
    cursor.execute("SELECT * FROM Companies WHERE company_id = %s", (session['company_id'],))
    company = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('edit_company_profile.html', company=company)

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Jobs (company_id, title, description, min_experience, salary_min, salary_max)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session['company_id'],
              request.form['title'],
              request.form['description'],
              request.form.get('min_experience', 0),
              request.form.get('salary_min'),
              request.form.get('salary_max')))
        
        job_id = cursor.lastrowid
        
        for skill_name, weight in zip(request.form.getlist('skills'), request.form.getlist('importance_weights')):
            if skill_name and weight:
                cursor.execute("SELECT skill_id FROM Skills WHERE skill_name = %s", (skill_name,))
                skill = cursor.fetchone()
                if skill:
                    skill_id = skill[0]
                else:
                    cursor.execute("INSERT INTO Skills (skill_name) VALUES (%s)", (skill_name,))
                    skill_id = cursor.lastrowid
                
                cursor.execute("""
                    INSERT INTO Job_Skills (job_id, skill_id, importance_weight) VALUES (%s, %s, %s)
                """, (job_id, skill_id, weight))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Job posted successfully!', 'success')
        return redirect(url_for('company_jobs'))
    
    return render_template('post_job.html')

@app.route('/company/edit_job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM Jobs WHERE job_id = %s AND company_id = %s
    """, (job_id, session['company_id']))
    job = cursor.fetchone()
    
    if not job:
        flash('Job not found or access denied', 'error')
        return redirect(url_for('company_jobs'))
    
    if request.method == 'POST':
        cursor.execute("""
            UPDATE Jobs 
            SET title = %s, description = %s, min_experience = %s, salary_min = %s, salary_max = %s
            WHERE job_id = %s AND company_id = %s
        """, (request.form['title'],
              request.form['description'],
              request.form.get('min_experience', 0),
              request.form.get('salary_min'),
              request.form.get('salary_max'),
              job_id, session['company_id']))
        conn.commit()
        
        cursor.execute("DELETE FROM Job_Skills WHERE job_id = %s", (job_id,))
        
        for skill_name, weight in zip(request.form.getlist('skills'), request.form.getlist('importance_weights')):
            if skill_name and weight:
                cursor.execute("SELECT skill_id FROM Skills WHERE skill_name = %s", (skill_name,))
                skill = cursor.fetchone()
                if skill:
                    skill_id = skill['skill_id']
                else:
                    cursor.execute("INSERT INTO Skills (skill_name) VALUES (%s)", (skill_name,))
                    skill_id = cursor.lastrowid
                
                cursor.execute("""
                    INSERT INTO Job_Skills (job_id, skill_id, importance_weight) VALUES (%s, %s, %s)
                """, (job_id, skill_id, weight))
        
        conn.commit()
        cursor.close()
        conn.close()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('company_jobs'))
    
    cursor.execute("""
        SELECT s.skill_name, js.importance_weight
        FROM Job_Skills js
        JOIN Skills s ON js.skill_id = s.skill_id
        WHERE js.job_id = %s
    """, (job_id,))
    job_skills = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('edit_job.html', job=job, job_skills=job_skills)

@app.route('/company/delete_job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT company_id FROM Jobs WHERE job_id = %s", (job_id,))
    result = cursor.fetchone()
    
    if not result or result[0] != session['company_id']:
        flash('Job not found or access denied', 'error')
        return redirect(url_for('company_jobs'))
    
    cursor.execute("DELETE FROM Job_Skills WHERE job_id = %s", (job_id,))
    cursor.execute("DELETE FROM Applications WHERE job_id = %s", (job_id,))
    cursor.execute("DELETE FROM Jobs WHERE job_id = %s", (job_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('company_jobs'))

@app.route('/view_applicants/<int:job_id>')
def view_applicants(job_id):
    if session.get('user_type') != 'company':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT j.*, c.company_name 
        FROM Jobs j
        JOIN Companies c ON j.company_id = c.company_id
        WHERE j.job_id = %s AND j.company_id = %s
    """, (job_id, session['company_id']))
    job = cursor.fetchone()
    
    if not job:
        flash('Job not found or access denied', 'error')
        return redirect(url_for('company_jobs'))
    
    cursor.execute("""
        SELECT DISTINCT
            u.user_id, u.name, u.email, u.degree, u.cgpa, u.graduation_year,
            a.status, a.applied_date, a.application_id,
            COALESCE(
                (SELECT SUM(us2.proficiency_level * js2.importance_weight)
                 FROM User_Skills us2
                 JOIN Job_Skills js2 ON us2.skill_id = js2.skill_id
                 WHERE us2.user_id = u.user_id AND js2.job_id = %s
                ), 0
            ) as match_score
        FROM Applications a
        JOIN Users u ON a.user_id = u.user_id
        WHERE a.job_id = %s AND a.status != 'cancelled'
        ORDER BY match_score DESC
    """, (job_id, job_id))
    applicants = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('applicants.html', job=job, applicants=applicants)

@app.route('/update_application_status', methods=['POST'])
def update_application_status():
    if session.get('user_type') != 'company':
        flash('Access denied', 'error')
        return redirect(url_for('login'))
    
    user_id = request.form.get('application_id')
    job_id = request.form.get('job_id')
    status = request.form.get('status')
    
    if not all([user_id, job_id, status]):
        flash('Missing required information', 'error')
        return redirect(url_for('company_jobs'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT j.company_id FROM Jobs j WHERE j.job_id = %s", (job_id,))
    job = cursor.fetchone()
    
    if not job or job['company_id'] != session['company_id']:
        flash('Permission denied', 'error')
        return redirect(url_for('company_jobs'))
    
    try:
        cursor.execute("""
            UPDATE Applications SET status = %s WHERE user_id = %s AND job_id = %s
        """, (status, user_id, job_id))
        conn.commit()
        flash(f'Application {status} successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('view_applicants', job_id=job_id))


# ==================== STUDENT SKILL MANAGEMENT ====================

@app.route('/manage_skills')
def manage_skills():
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT s.skill_id, s.skill_name, s.category, 
               us.proficiency_level, us.years_experience
        FROM User_Skills us
        JOIN Skills s ON us.skill_id = s.skill_id
        WHERE us.user_id = %s
        ORDER BY s.skill_name
    """, (session['user_id'],))
    user_skills = cursor.fetchall()
    
    cursor.execute("""
        SELECT s.skill_id, s.skill_name, s.category
        FROM Skills s
        WHERE s.skill_id NOT IN (SELECT skill_id FROM User_Skills WHERE user_id = %s)
        ORDER BY s.skill_name
    """, (session['user_id'],))
    available_skills = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('manage_skills.html',
                         user_skills=user_skills,
                         available_skills=available_skills)

@app.route('/add_skill', methods=['POST'])
def add_skill():
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO User_Skills (user_id, skill_id, proficiency_level, years_experience)
            VALUES (%s, %s, %s, %s)
        """, (session['user_id'],
              request.form.get('skill_id'),
              request.form.get('proficiency_level', 3),
              request.form.get('years_experience', 0)))
        conn.commit()
        flash('Skill added successfully!', 'success')
    except mysql.connector.IntegrityError:
        flash('You already have this skill!', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('manage_skills'))

@app.route('/update_skill/<int:skill_id>', methods=['POST'])
def update_skill(skill_id):
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE User_Skills 
        SET proficiency_level = %s, years_experience = %s
        WHERE user_id = %s AND skill_id = %s
    """, (request.form.get('proficiency_level'),
          request.form.get('years_experience'),
          session['user_id'], skill_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Skill updated successfully!', 'success')
    return redirect(url_for('manage_skills'))

@app.route('/remove_skill/<int:skill_id>', methods=['POST'])
def remove_skill(skill_id):
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM User_Skills WHERE user_id = %s AND skill_id = %s",
                  (session['user_id'], skill_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Skill removed successfully!', 'success')
    return redirect(url_for('manage_skills'))

@app.route('/add_new_skill', methods=['POST'])
def add_new_skill():
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    skill_name = request.form.get('skill_name')
    category = request.form.get('category', 'General')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO Skills (skill_name, category) VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE skill_id = LAST_INSERT_ID(skill_id)
        """, (skill_name, category))
        skill_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO User_Skills (user_id, skill_id, proficiency_level, years_experience)
            VALUES (%s, %s, %s, %s)
        """, (session['user_id'], skill_id,
              request.form.get('proficiency_level', 3),
              request.form.get('years_experience', 0)))
        conn.commit()
        flash(f'Skill "{skill_name}" added successfully!', 'success')
    except mysql.connector.IntegrityError:
        flash('You already have this skill!', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('manage_skills'))

@app.route('/get_job_skills/<int:job_id>')
def get_job_skills(job_id):
    """API endpoint to get job skills for modal"""
    conn = get_db_connection()
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
    
    return {"skills": skills}


# ==================== RUN APP ====================

if __name__ == '__main__':
    app.run(debug=True)