# databases.py
from flask import session
import random
import sqlite3
from datetime import datetime

class User:
    def __init__(self):
        # Initialize database connections
        self.init_users_database()
        self.init_user_database()

    def init_users_database(self):
        """Initialize the SQLite users.db database"""
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Create users table with the same structure as SQLAlchemy
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL
        )
        """
        
        try:
            cursor.execute(create_table_query)
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_user_by_email(self, email):
        """Fetch user by email"""
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name, email, password FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'name': user[1],
                    'email': user[2],
                    'password': user[3]
                }
            return None
        finally:
            cursor.close()
            conn.close()

    def create_user(self, name, email, password):
        """Create a new user in users.db"""
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()
            return {
                'id': cursor.lastrowid,
                'name': name,
                'email': email,
                'password': password
            }
        finally:
            cursor.close()
            conn.close()

    def create_session(self, user):
        """Create session data exactly as in original code"""
        session_id = random.randint(10000, 99999)
        session["session_id"] = session_id
        session["user_id"] = user['id']
        session["session_counter"] = session.get("session_counter", 0) + 1

        session_data = {
            "session_id": session_id,
            "user_id": user['id'],
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "counter": session["session_counter"]
        }

        return session_data

    def init_user_database(self):
        """Initialize the main user database table - keeping original structure"""
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS USER_DATABASE (
            user_id INTEGER PRIMARY KEY,
            session_id INTEGER
        )
        """
        
        try:
            cursor.execute(create_table_query)
            conn.commit()
            print("USER_DATABASE table created successfully.")
        except Exception as e:
            print(f"Error creating USER_DATABASE table: {e}")
        finally:
            cursor.close()
            conn.close()

    def register_user_in_main_db(self, user_id, session_id):
        """Register user in the main database - keeping original structure"""
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO USER_DATABASE (user_id, session_id) VALUES (?, ?)",
                (user_id, session_id)
            )
            conn.commit()
            print(f"User {user_id} registered in main database with session {session_id}")
        except Exception as e:
            print(f"Error registering user in main database: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def create_user_specific_tables(self, user_id, session_id):
        """Create user-specific tables - keeping original structure"""
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        
        table_name_conversations = f"Table_{user_id}_conversations"
        table_name_health_data = f"Table_{user_id}_health_data"
        
        try:
            # Create conversations table with original structure
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name_conversations} (
                    session_id TEXT PRIMARY KEY,
                    conversation_summary TEXT
                )
            """)
            
            # Create health data table with original structure
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name_health_data} (
                    health_parameters TEXT,
                    social_parameters TEXT,
                    environmental_parameters TEXT
                )
            """)
            
            # Insert initial session record as in original
            cursor.execute(f"""
                INSERT INTO {table_name_conversations} (session_id, conversation_summary)
                VALUES (?, '')
            """, (str(session_id),))
            
            conn.commit()
            print(f"User-specific tables created for user {user_id}")
        except Exception as e:
            print(f"Error creating user-specific tables: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()