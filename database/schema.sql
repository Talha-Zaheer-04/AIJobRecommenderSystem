-- =====================================================
-- AI Job Recommendation System - Database Schema
-- =====================================================

-- Create database (if not exists)
CREATE DATABASE IF NOT EXISTS sem_proj;
USE sem_proj;

-- =====================================================
-- 1. USERS TABLE (Students)
-- =====================================================
CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,  -- Added password field
    degree VARCHAR(255),
    cgpa DECIMAL(3,2),
    graduation_year INT
);

-- =====================================================
-- 2. SKILLS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS Skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(255)
);

-- =====================================================
-- 3. COMPANIES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS Companies (
    company_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    industry VARCHAR(255),
    location VARCHAR(255)
);

-- =====================================================
-- 4. JOBS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS Jobs (
    job_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    min_experience INT,
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_jobs_company
        FOREIGN KEY (company_id) REFERENCES Companies(company_id) ON DELETE CASCADE
);

-- =====================================================
-- 5. USER_SKILLS TABLE (Student Skills Mapping)
-- =====================================================
CREATE TABLE IF NOT EXISTS User_Skills (
    user_id INT NOT NULL,
    skill_id INT NOT NULL,
    proficiency_level INT,
    years_experience INT,
    PRIMARY KEY (user_id, skill_id),
    CONSTRAINT chk_user_skills_proficiency
        CHECK (proficiency_level BETWEEN 1 AND 5),
    CONSTRAINT fk_user_skills_user
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_user_skills_skill
        FOREIGN KEY (skill_id) REFERENCES Skills(skill_id) ON DELETE CASCADE
);

-- =====================================================
-- 6. JOB_SKILLS TABLE (Job Requirements Mapping)
-- =====================================================
CREATE TABLE IF NOT EXISTS Job_Skills (
    job_id INT NOT NULL,
    skill_id INT NOT NULL,
    importance_weight INT,
    PRIMARY KEY (job_id, skill_id),
    CONSTRAINT chk_job_skills_importance
        CHECK (importance_weight BETWEEN 1 AND 5),
    CONSTRAINT fk_job_skills_job
        FOREIGN KEY (job_id) REFERENCES Jobs(job_id) ON DELETE CASCADE,
    CONSTRAINT fk_job_skills_skill
        FOREIGN KEY (skill_id) REFERENCES Skills(skill_id) ON DELETE CASCADE
);

-- =====================================================
-- 7. APPLICATIONS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS Applications (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    job_id INT NOT NULL,
    status VARCHAR(100) DEFAULT 'pending',
    applied_date DATE,
    CONSTRAINT uq_applications_user_job
        UNIQUE (user_id, job_id),
    CONSTRAINT fk_applications_user
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_applications_job
        FOREIGN KEY (job_id) REFERENCES Jobs(job_id) ON DELETE CASCADE
);

-- =====================================================
-- Inserting Sample Data
-- =====================================================

-- Sample Users (passwords are 'password123')
INSERT INTO Users (name, email, password, degree, cgpa, graduation_year) VALUES
('Abdul Azeez', 'abdul.azeez@nu.edu.pk', 'temp123', 'Computer Science', 3.20, 2025),
('Muhammad Talha Zaheer', 'talha.zaheer@nu.edu.pk', 'temp123', 'Artificial Intelligence', 3.4, 2024),
('Muhammad Mubeen Haider', 'mubeen.haider@nu.edu.pk', 'temp123', 'Computer Science', 3.30, 2025);

-- Sample Skills
INSERT INTO Skills (skill_name, category) VALUES
('Python', 'Programming'),
('SQL', 'Database'),
('Java', 'Programming'),
('JavaScript', 'Frontend'),
('Machine Learning', 'AI/ML'),
('TensorFlow', 'AI/ML'),
('React', 'Frontend'),
('Django', 'Backend'),
('Communication', 'Soft Skill'),
('Project Management', 'Management');

-- Sample Companies
INSERT INTO Companies (company_name, email, password, industry, location) VALUES
('TechCorp', 'techcorp@techcorp.com', 'temp123', 'IT Services', 'Islamabad'),
('DataWorks', 'dataworks@dataworks.com', 'temp123', 'Analytics', 'Lahore'),
('Innovate Inc', 'innovate@innovate.com', 'temp123', 'Software', 'Karachi');

-- Sample Jobs
INSERT INTO Jobs (company_id, title, description, min_experience, salary_min, salary_max) VALUES
(1, 'Junior Python Dev', 'Build APIs and scripts using Python and SQL', 0, 70000, 90000),
(1, 'SQL Analyst', 'Write complex queries and optimize database performance', 1, 75000, 95000),
(2, 'ML Intern', 'Work on prediction models and data analysis', 0, 60000, 80000),
(3, 'Full Stack Dev', 'Develop web applications using Java and React', 2, 85000, 110000);

-- Sample User_Skills (Alice - user_id=1)
INSERT INTO User_Skills (user_id, skill_id, proficiency_level, years_experience) VALUES
(1, 1, 5, 2),  -- Python
(1, 2, 4, 1),  -- SQL
(1, 5, 4, 2); -- Machine Learning

-- Sample User_Skills (Bob - user_id=2)
INSERT INTO User_Skills (user_id, skill_id, proficiency_level, years_experience) VALUES
(2, 2, 4, 1),  -- SQL
(2, 3, 3, 1);  -- Java

-- Sample User_Skills (Carol - user_id=3)
INSERT INTO User_Skills (user_id, skill_id, proficiency_level, years_experience) VALUES
(3, 1, 4, 1),  -- Python
(3, 3, 4, 1);  -- Java

-- Sample Job_Skills
INSERT INTO Job_Skills (job_id, skill_id, importance_weight) VALUES
(1, 1, 5),  -- Junior Python Dev needs Python
(1, 2, 3),  -- Junior Python Dev needs SQL
(2, 2, 5),  -- SQL Analyst needs SQL
(3, 1, 4),  -- ML Intern needs Python
(3, 5, 5),  -- ML Intern needs Machine Learning
(4, 1, 4),  -- Full Stack Dev needs Python
(4, 3, 5);  -- Full Stack Dev needs Java

-- Sample Applications
INSERT INTO Applications (user_id, job_id, status, applied_date) VALUES
(1, 1, 'accepted', CURDATE()),
(2, 2, 'pending', CURDATE());
