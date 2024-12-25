from flask import session
import random
import sqlite3
from datetime import datetime

class User:
    def __init__(self):
        # Initialize database connections
        self.init_users_database()
        self.init_user_database()
        self.session_data = {}

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

        self.session_data = {
            "session_id": session_id,
            "user_id": user['id'],
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "counter": session["session_counter"],
            "user":["Hi, I was looking for a good friend"],
            "llm":["Hi how are you?"],
        }

        return self.session_data

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
                (user_id, self.session_data["session_id"])
            )
            conn.commit()
            print(f"User {user_id} registered in main database with session {self.session_data["session_id"]}")
        except Exception as e:
            print(f"Error registering user in main database: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def extract_user_database(self, user_id): # Columnwise Extract all the data fields
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        
        conversations_table = f"Table_{user_id}_conversations"
        health_data_table = f"Table_{user_id}_health_data"

        # select * from table conversations_table:
        cursor.execute(f"""
            SELECT * FROM {conversations_table}
        """)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        output1 = ""
        for col_index, col_name in enumerate(columns):
            output1 += (f"{col_name}:")
            for row in rows:
                output1 += f"  {row[col_index]}, "[:-2]
        
        # select * from table health_data_table:
        cursor.execute(f"""
            SELECT * FROM {health_data_table}
        """)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        output2 = ""
        for col_index, col_name in enumerate(columns):
            output2 += (f"{col_name}:")
            for row in rows:
                output2 += f"  {row[col_index]}, "[:-2] 

        user_data = f"Previous Conversations: {output1}\n\n\n Health Data:{output2}"
        return user_data

    def add_to_table1(self, conversation_summary):
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        session_id = self.session_data["session_id"]
        user_id = self.session_data["user_id"]
        table_name = f"Table_{user_id}_conversations"

        try:
            # Assuming the table has columns `session_id` and `conversation_summary`
            query = f"INSERT INTO {table_name} (session_id, conversation_summary) VALUES (?, ?)"
            cursor.execute(query, (session_id, conversation_summary))
            conn.commit()
            print(f"Added to: {table_name}; \nThe Summary: {conversation_summary}")

        except Exception as e:
            print(f"Error occurred: {e}")
            raise e

        finally:
            # Ensure resources are cleaned up
            conn.close()

    # TODO: Implement the diagram into code:
    def add_to_table2(self):
        pass

    def create_user_specific_tables(self, user_id, session_id):
        user_id = self.session_data['user_id']
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
            # cursor.execute(f"""
            #     CREATE TABLE IF NOT EXISTS {table_name_health_data} (
            #         health_parameters TEXT,
            #         social_parameters TEXT,
            #         environmental_parameters TEXT
            #     )
            # """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name_health_data} (
                    ID INT PRIMARY KEY AUTO_INCREMENT, -- Unique identifier for each entry
                    Name VARCHAR(100),
                    Age INT,
                    Sex VARCHAR(10),
                    Ethnicity VARCHAR(100),
                    
                    SavedConversations TEXT,
                    ImportantDataRichConversations TEXT,
                    Logic VARCHAR(100),
                    DataExtractedFromPreviousSessions TEXT,
                    
                    SocialParameters_IncomeStatus VARCHAR(100),
                    SocialParameters_WorkLife VARCHAR(100),
                    SocialParameters_EducationalBackground VARCHAR(100),
                    SocialParameters_FamilyStatus VARCHAR(100),
                    SocialParameters_MaritalStatus VARCHAR(100),
                    SocialParameters_Children VARCHAR(100),
                    SocialParameters_Hobbies TEXT,
                    SocialParameters_FuturePlans TEXT,
                    SocialParameters_LivingEnvironment TEXT,
                    SocialParameters_SupportNetwork TEXT,
                    SocialParameters_CulturalBackground TEXT,
                    SocialParameters_OccupationType VARCHAR(100),
                    SocialParameters_FinancialStability VARCHAR(100),
                    SocialParameters_DailyRoutine TEXT,
                    
                    HealthParameters_HealthHistory TEXT,
                    HealthParameters_RecentHealthProblems TEXT,
                    HealthParameters_FamilyHealthRecord TEXT,
                    HealthParameters_Diet TEXT,
                    HealthParameters_ExerciseRoutine TEXT,
                    HealthParameters_MentalHealthHistory TEXT,
                    HealthParameters_SleepPatterns TEXT,
                    HealthParameters_MedicationAndSupplementUse TEXT,
                    HealthParameters_SubstanceUse TEXT,
                    HealthParameters_AllergiesAndSensitivities TEXT,
                    HealthParameters_ImmunizationStatus TEXT,
                    HealthParameters_SurgicalHistory TEXT,
                    HealthParameters_ChronicConditions TEXT,
                    HealthParameters_GeneticFactors TEXT,
                    HealthParameters_ReproductiveHealth TEXT,
                    HealthParameters_PainManagement TEXT,
                    HealthParameters_HydrationHabits TEXT,
                    HealthParameters_MobilityAndFunctionalLimitations TEXT,
                    
                    EnvironmentalParameters_LivingEnvironment TEXT,
                    EnvironmentalParameters_ClimateExposure TEXT,
                    EnvironmentalParameters_WorkplaceEnvironment TEXT,
                    EnvironmentalParameters_AccessToHealthcare TEXT,
                    EnvironmentalParameters_FoodAndWaterQuality TEXT
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