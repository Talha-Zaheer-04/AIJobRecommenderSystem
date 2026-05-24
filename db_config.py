# db_config.py
"""
Database Configuration Module
Handles MySQL database connections for the application
"""

import mysql.connector
from mysql.connector import Error

# ==================== CONFIGURATION ====================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',           # Your MySQL password (leave empty if none)
    'database': 'sem_proj'    # Your database name
}


# ==================== CONNECTION FUNCTION ====================

def get_db_connection():
    """
    Establish and return a MySQL database connection
    
    Returns:
        MySQL connection object if successful, None otherwise
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


# ==================== HELPER FUNCTIONS ====================

def test_connection():
    """
    Test the database connection
    Returns True if connection successful, False otherwise
    """
    conn = get_db_connection()
    if conn:
        conn.close()
        return True
    return False


def get_connection_info():
    """
    Get connection information (without password)
    Returns dictionary with connection details
    """
    return {
        'host': DB_CONFIG['host'],
        'user': DB_CONFIG['user'],
        'database': DB_CONFIG['database']
    }