# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from Databases import User
import pathlib
# RAG dependencies
import rag as r
import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
from google.oauth2 import id_token
import cachecontrol
import requests
temp_dir = rf"{os.getenv("Template_path")}"
static_dir = rf"{os.getenv("Static_path")}"

app = Flask(__name__, template_folder=temp_dir, static_folder=static_dir)
load_dotenv()
app.config['SECRET_KEY'] = 'your_secret_key'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

GOOGlE_CLIENT_ID = os.getenv("google_client_id")

client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email","openid"],
    redirect_uri="http://127.0.0.1:5000/callback")

# Initialize User class
user_manager = User()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_api_key', methods=['GET'])
def get_api_key():
    # Only return the API key if the user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Retrieve the API key from environment variables
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'error': 'API key not configured'}), 500
    
    return jsonify({'api_key': api_key})
    
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
        print("\n\n\n\n\nSESSION IS CREATED SUCCESSFULLY\n\n\n")
        print(user_manager.session_data)
        flash(f"Welcome {user['name']}! Session started.")
        return redirect(url_for('coming_soon', session_id=session_data_login["session_id"]))
    else:
        flash('Invalid email or password. Please try again.')
        return redirect(url_for('index'))

@app.route('/interact', methods=['GET', 'POST'])
def interact():
    # Initializing Rag & Embedding Space Objects:
    rag_object = r.RAG(os.getenv("GEMINI_API_KEY"))
    rag_data = r.DataHandler(os.getenv("VOYAGE_API_KEY"))
    # Initilizing the string variables:
    User_text, search_output, Previous_conversation = "", "", ""

    # Form Interactions:
    if request.method == 'POST':
        # User's text input:
        User_text = request.form.get("User_text")
        print(f"Text recieved: {User_text}")
        # Vector Search:
        search_output_list = rag_data.hybrid_search(query=User_text, top_k=3)
        search_output = search_output_list.join()
        # Previous Conversations from the session_date:
        user_history = user_manager.session_data["user"]
        llm_history = user_manager.session_data["llm"]

        length = len(llm_history)
        for i in range(0,length):
            Previous_conversation = [f"User: {user_history[i]} \nDiagnAI:{llm_history[i]}\n\n"]
        Previous_conversation = Previous_conversation.join()

    # TODO: Dynamic Prompting

    # Selecting the model:
    rag_object.gemini_model = rag_object.gemini_models[0]

    # Send in the pipeline:
    response = rag_object.generate_response_gemini(
                    rag_object.final_wrapper_prompt(search_output,
                        User_text,
                        Previous_conversation))

    print(response)

    # TODO – Parse the output:
    parsed_data = response # placeholder for the parsed data from the llm, just to make it work for now

    # TODO – Convert it into speech:
    speech = "" # this is placeholder for the audio file

    # Store these in session_id dictionary:
    user_manager.session_data["user"].append(User_text)
    user_manager.session_data["llm"].append(parsed_data)

    # Show through the text output:
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('index'))

    return render_template('interact.html',response_text=parsed_data, speech=speech)


@app.route('/session-end', methods=['POST'])
def session_end():
    # Handle the session end event here
    rag_object = r.RAG(os.getenv("GEMINI_API_KEY"))
    summary = rag_object.conversations_summarizer(user_manager.session_data["user"], user_manager.session_data["llm"])
    
    User.add_to_table1(summary)

    print("User session ended")
    return '', 204

@app.route('/google-login')
def google_login():
    auth_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(auth_url)

@app.route('/callback')
def callback():
    try:
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        
        request_session = requests.Session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        id_info = id_token.verify_oauth2_token(
            id_token=credentials.id_token,
            request=token_request,
            audience=GOOGlE_CLIENT_ID
        )

        email = id_info.get("email")
        name = id_info.get("name")
        
        # Check if user exists
        user = user_manager.get_user_by_email(email)
        if not user:
            # Create dummy password hash for Google users
            google_password = generate_password_hash(f"google_{id_info['sub']}")
            user = user_manager.create_user(name, email, google_password)
        
        session_data = user_manager.create_session(user)
        user_manager.register_user_in_main_db(user['id'], session_data["session_id"])
        user_manager.create_user_specific_tables(user['id'], session_data["session_id"])
        
        session["google_id"] = id_info.get("sub")
        session["name"] = name
        session["user_id"] = user['id']
        session["session_id"] = session_data["session_id"]
        
        return redirect(url_for('coming_soon', session_id=session_data["session_id"]))
        
    except Exception as e:
        print(f"Auth error: {str(e)}")
        return abort(500, str(e))

@app.route('/coming_soon')
def coming_soon():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('index'))
    return render_template('coming_soon.html')

#returning session_id for js
@app.route('/get_session_id')
def get_session_id():
    return jsonify({'session_id': session['session_id']})


if __name__ == '__main__':
    app.run(debug=True)
    