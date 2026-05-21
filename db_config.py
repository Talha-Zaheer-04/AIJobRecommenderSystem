# db_config.py
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",           # Your MySQL username
            password="",           # Your MySQL password (leave empty if none)
            database="sem_proj"  # Your database name
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None