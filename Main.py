from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import random
from datetime import datetime
import sqlite3

app = Flask(__name__)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model for SQLite DB
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

def create_session(user):
    session_id = random.randint(10000, 99999)
    session["session_id"] = session_id
    session["user_id"] = user.id  
    session["session_counter"] = session.get("session_counter", 0) + 1

    session_data = {
        "session_id": session_id,  # Changed from Session_ID to match the usage
        "user_id": user.id,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "counter": session["session_counter"]
    }

    return session_data

def init_user_database():
    """Initialize the main user database table"""
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

def register_user_in_main_db(user_id, session_id):
    """Register user in the main database"""
    conn = sqlite3.connect('Main.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO USER_DATABASE (user_id, session_id) VALUES (?, ?)",
                      (user_id, session_id))
        conn.commit()
        print(f"User {user_id} registered in main database with session {session_id}")
    except Exception as e:
        print(f"Error registering user in main database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def create_user_specific_tables(user_id, session_id):
    """Create user-specific tables"""
    conn = sqlite3.connect('Main.db')
    cursor = conn.cursor()
    
    table_name_conversations = f"Table_{user_id}_conversations"
    table_name_health_data = f"Table_{user_id}_health_data"
    
    try:
        # Create conversations table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name_conversations} (
                session_id TEXT PRIMARY KEY,
                conversation_summary TEXT
            )
        """)
        
        # Create health data table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name_health_data} (
                health_parameters TEXT,
                social_parameters TEXT,
                environmental_parameters TEXT
            )
        """)
        
        # Insert initial session record
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.')
            return redirect(url_for('index'))

        try:
            # Create user in SQLAlchemy DB
            hashed_password = generate_password_hash(password)
            new_user = User(name=name, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            # Create session
            session_data = create_session(new_user)
            
            # Register in main database and create user-specific tables
            register_user_in_main_db(new_user.id, session_data["session_id"])
            create_user_specific_tables(new_user.id, session_data["session_id"])

            flash('Registration successful! Please log in.')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}')
            return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session_data = create_session(user)
        flash(f"Welcome {user.name}! Session started.")
        return redirect(url_for('coming_soon', session_id=session_data["session_id"]))
    else:
        flash('Invalid email or password. Please try again.')
        return redirect(url_for('index'))

@app.route('/coming_soon')
def coming_soon():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('index'))
    return render_template('coming_soon.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_user_database()  # Initialize the main user database table
    app.run(debug=True)
