import os
os.load_dotenv()

import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")
response = model.generate_content("Explain how AI works")
print(response.text)