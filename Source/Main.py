# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from Databases import User

# RAG dependencies
import rag as r
import os
from dotenv import load_dotenv

template_dir = r'C:\Users\sufya\OneDrive\Desktop\DiagnAI\templates'
static_dir = r'C:\Users\sufya\OneDrive\Desktop\DiagnAI\static'


app = Flask(__name__,
            template_folder=template_dir,
            static_folder=static_dir)


load_dotenv()
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

            # Create session dictionary immediately after registration"
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
        # Create session dictionary immediately upon successful login
        session_data_login = user_manager.create_session(user)
        flash(f"Welcome {user['name']}! Session started.")
        return redirect(url_for('coming_soon', session_id=session_data_login["session_id"]))
    else:
        flash('Invalid email or password. Please try again.')
        return redirect(url_for('index'))

@app.route('/interact', methods=['GET', 'POST'])
def interact():
    # Initializing Rag & Embedding Space Objects:
    rag_object = r.RAG(os.getenv("CLAUDE_KEY"))
    voyage_object = r.VoyageEmbedding(os.getenv("VOYAGE_API_KEY"))
    # Initilizing the string variables:
    User_text, search_output, Previous_conversation = "", "", ""

    # Form Interactions:
    if request.method == 'POST':
        # User's text input:
        User_text = request.form.get("User_text")
        # Vector Search:
        search_output_list = voyage_object.hybrid_search(query=User_text, top_k=3)
        search_output = search_output_list.join()
        # Previous Conversations from the session_date:
        user_history = user_manager.session_data["user"]
        llm_history = user_manager.session_data["llm"]

        length = len(llm_history)
        for i in range(0,length):
            Previous_conversation = [f"User: {user_history[i]} \nDiagnAI:{llm_history[i]}\n\n"]
        Previous_conversation = Previous_conversation.join()     

    # Send in the pipeline:
    response = rag_object.generate_response(
                    rag_object.final_wrapper_prompt(f"{search_output}",
                   f"{User_text}",
                   f"{Previous_conversation}"))

    print(response)

    # TODO – Parse the output:
    parsed_data = "" # placeholder for the parsed data from the llm

    # TODO – Convert it into speech:
    speech = "" # this is placeholder for the audio file

    # TODO – Store these in session_id dictionary:
    user_manager.session_data["user"].append(User_text)
    user_manager.session_data["llm"].append(parsed_data)

    # Show through the text output:
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('index'))

    return render_template('interact.html',response_text=parsed_data, speech=speech)

@app.route('/coming_soon')
def coming_soon():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('index'))
    return render_template('coming_soon.html')

if __name__ == '__main__':
    app.run(debug=True)