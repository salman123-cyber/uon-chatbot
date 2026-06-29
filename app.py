# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__, template_folder='templates')
CORS(app)  # Allows your frontend widget to talk to the backend without CORS blocks

# 1. API Configuration Parameters
GEMINI_API_KEY = "AQ.Ab8RN6IY3C-yXh6SAlNHovj9_DJF-MlPZmbiRSfFL1oNl-LJcA"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

# Helper function to read the text policy guidelines safely
def load_text_policies():
    filename = 'uon_knowledge.txt'
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    return "Descriptive admission rules and policies file missing."

# Helper function to read and load the normalized merit lists JSON array
def load_json_merits():
    filename = 'merits_data_normalized.json'
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data)  # Minifies whitespace for faster API performance
        except Exception as e:
            return f"Error reading merit JSON data: {e}"
    return "Historical merit lists dataset file missing."

@app.route('/api/chat', methods=['POST'])
def chat():
    user_data = request.json or {}
    user_message = user_data.get('message', '').strip()

    if not user_message:
        return jsonify({"error": "Empty message received"}), 400

    # 2. Extract context from both data files simultaneously
    policies_context = load_text_policies()
    merits_context = load_json_merits()

    # Core System Prompt Framing and Guardrails
    system_base = (
        "You are the official AI Admission Assistant for the University of Narowal (UON).\n"
        "Ground your responses strictly using the data context blocks provided below.\n"
        "Keep your answers short, professional, welcoming, and under 3-4 lines.\n"
        "When asked about closing merits, opening merits, cutoffs, or departments, look closely at the historical trends provided in the JSON block.\n"
        "If a student's inquiry is missing from the provided datasets, say: \n"
        "'I don't have that specific data right now. Please keep checking the official notice boards at uon.edu.pk or contact admissions@uon.edu.pk.'\n"
    )

    # 3. Construct payload injecting both data sets cleanly into Gemini
    combined_prompt = (
        f"{system_base}\n\n"
        f"### CONTEXT 1: ADMISSION POLICIES & ADMINISTRATIVE DETAILS:\n{policies_context}\n\n"
        f"### CONTEXT 2: HISTORICAL MERIT LIST DATA (JSON FORMAT):\n{merits_context}\n\n"
        f"### STUDENT QUESTION:\n{user_message}"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": combined_prompt}]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_URL, json=payload, headers={"Content-Type": "application/json"})
        response_data = response.json()

        if "error" in response_data:
            print(f"Google Gateway Error: {response_data['error']['message']}")
            return jsonify({"reply": "System optimization underway. Please try again shortly."}), 500

        bot_reply = response_data['candidates'][0]['content']['parts'][0]['text']
        return jsonify({"reply": bot_reply})

    except Exception as e:
        print(f"Execution Exception Traced: {e}")
        return jsonify({"reply": "Connection variance detected. Please re-submit your prompt."}), 500

@app.route('/')
def home():
    # Verify the template exists before trying to render it
    template_path = os.path.join(app.template_folder, 'index.html')
    if not os.path.exists(template_path):
        return f"Debug Info: Looking for template at {template_path}. Folder items: {os.listdir(app.template_folder) if os.path.exists(app.template_folder) else 'Folder not found'}"
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
