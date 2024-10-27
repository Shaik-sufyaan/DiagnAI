import streamlit as st
import requests

st.title("Flask with Streamlit Example")

# Call the Flask API
response = requests.get('http://127.0.0.1:5000/data')
data = response.json()

# Display the data in Streamlit
st.write(data['message'])
st.write("Numbers:", data['numbers'])
