# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from Databases import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize User class
user_manager = User()

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
        if user_manager.get_user_by_email(email):
            flash('Email already registered. Please log in.')
            return redirect(url_for('index'))

        try:
            # Create user with hashed password
            hashed_password = generate_password_hash(password)
            new_user = user_manager.create_user(name, email, hashed_password)

            # Create session immediately after registration
            session_data = user_manager.create_session(new_user)
            
            # Register in main database and create user-specific tables
            user_manager.register_user_in_main_db(new_user['id'], session_data["session_id"])
            user_manager.create_user_specific_tables(new_user['id'], session_data["session_id"])

            flash('Registration successful! Please log in.')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Registration failed: {str(e)}')
            return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = user_manager.get_user_by_email(email)
    if user and check_password_hash(user['password'], password):
        # Create session immediately upon successful login
        session_data = user_manager.create_session(user)
        flash(f"Welcome {user['name']}! Session started.")
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
    app.run(debug=True)