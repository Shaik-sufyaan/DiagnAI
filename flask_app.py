from flask import Flask, request, render_template, session, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import threading
import anthropic
import time
import hashlib
import json
from functools import wraps
from RagPipeline import main as rag_main

app = Flask(__name__)
app.secret_key = 'dev_secret_key_123'  # Simple dev secret key as requested

client = anthropic.Client('your-api-key')  # Replace with your Claude API key

# Database initialization
def init_db():
    conn = sqlite3.connect('user_sessions.db')
    c = conn.cursor()
    
    # Create User_data table
    c.execute('''
        CREATE TABLE IF NOT EXISTS User_data (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            User_Name TEXT UNIQUE NOT NULL,
            Password TEXT NOT NULL,
            DOB DATE NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# Create user-specific table
def create_user_table(user_id):
    conn = sqlite3.connect('user_sessions.db')
    c = conn.cursor()
    
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS User_{user_id}_sessions (
            Session_ID TEXT PRIMARY KEY,
            Start_time TIMESTAMP,
            End_time TIMESTAMP,
            Conversation_Summary TEXT,
            FOREIGN KEY (Session_ID) REFERENCES User_data(UserID)
        )
    ''')
    
    conn.commit()
    conn.close()

# Password hashing function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Session management
active_sessions = {}

def check_session_timeout():
    while True:
        current_time = datetime.now()
        for session_id in list(active_sessions.keys()):
            if (current_time - active_sessions[session_id]['last_activity']) > timedelta(minutes=2):
                end_session(session_id)
        time.sleep(60)  # Check every minute

# Start session timeout checker in a separate thread
timeout_thread = threading.Thread(target=check_session_timeout, daemon=True)
timeout_thread.start()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Update last activity
def update_activity():
    if 'session_id' in session:
        active_sessions[session['session_id']]['last_activity'] = datetime.now()

# Summarize conversation using Claude
def summarize(conversation):
    try:
        # Format conversation for summarization
        conv_text = "\n".join([
            f"User: {msg['input']}\nAssistant: {msg['output']}"
            for msg in conversation
        ])
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"Please summarize this conversation concisely: {conv_text}"
            }]
        )
        return response.content
    except Exception as e:
        return f"Error in summarization: {str(e)}"

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        dob = request.form['dob']
        
        conn = sqlite3.connect('user_sessions.db')
        c = conn.cursor()
        
        try:
            c.execute('INSERT INTO User_data (User_Name, Password, DOB) VALUES (?, ?, ?)',
                     (username, password, dob))
            user_id = c.lastrowid
            create_user_table(user_id)
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists!"
        finally:
            conn.close()
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        conn = sqlite3.connect('user_sessions.db')
        c = conn.cursor()
        
        c.execute('SELECT UserID FROM User_data WHERE User_Name = ? AND Password = ?',
                 (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['session_id'] = f"{user[0]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            active_sessions[session['session_id']] = {
                'last_activity': datetime.now(),
                'conversation': [],
                'current_summary': ""  # Track current conversation summary
            }
            
            # Record session start
            conn = sqlite3.connect('user_sessions.db')
            c = conn.cursor()
            c.execute(f'''
                INSERT INTO User_{user[0]}_sessions 
                (Session_ID, Start_time) 
                VALUES (?, ?)
            ''', (session['session_id'], datetime.now()))
            conn.commit()
            conn.close()
            
            return redirect(url_for('dashboard'))
        
        return "Invalid credentials!"
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    update_activity()
    return render_template('dashboard.html')

@app.route('/process', methods=['POST'])
@login_required
def process():
    update_activity()
    input_text = request.form['input_text']
    
    # Get current session data
    session_data = active_sessions[session['session_id']]
    
    # Get current conversation summary
    current_summary = session_data['current_summary']
    
    # Process with RAG
    try:
        # Call your RAG function with input and current conversation summary
        result = rag_main(PromptIn=input_text, conv_history=current_summary)
        
        # Store conversation
        session_data['conversation'].append({
            'input': input_text,
            'output': result,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update conversation summary
        session_data['current_summary'] = summarize(session_data['conversation'])
        
        return result
        
    except Exception as e:
        return f"Error processing request: {str(e)}"

def end_session(session_id):
    if session_id in active_sessions:
        # Get final conversation summary
        summary = active_sessions[session_id]['current_summary']
        
        # Update database
        conn = sqlite3.connect('user_sessions.db')
        c = conn.cursor()
        user_id = session_id.split('_')[0]
        
        c.execute(f'''
            UPDATE User_{user_id}_sessions 
            SET End_time = ?, Conversation_Summary = ?
            WHERE Session_ID = ?
        ''', (datetime.now(), summary, session_id))
        
        conn.commit()
        conn.close()
        
        # Clean up session
        del active_sessions[session_id]

@app.route('/logout')
@login_required
def logout():
    if 'session_id' in session:
        end_session(session['session_id'])
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)