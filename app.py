import os
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__, template_folder='templates')
CORS(app)

API_KEY = os.environ.get("GCP_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "uon_knowledge.txt")
MERITS_PATH = os.path.join(BASE_DIR, "merits_data_normalized.json")

def load_knowledge_base():
    if os.path.exists(KNOWLEDGE_PATH):
        try:
            with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return "Error reading text context asset."
    return "Default Context: University of Narowal Admissions Portal."

def load_merits_data():
    if os.path.exists(MERITS_PATH):
        try:
            with open(MERITS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

@app.route('/', methods=['GET'])
def home():
    try:
        # Fallback debug directly on screen if templates get lost in Vercel cache
        template_file = os.path.join(BASE_DIR, 'templates', 'index.html')
        if not os.path.exists(template_file):
            return f"System Path Error: index.html not found at {template_file}. Current root contents: {os.listdir(BASE_DIR)}"
        return render_template('index.html')
    except Exception as e:
        return f"Unexpected Engine Error: {str(e)}"

@app.route('/api/chat', methods=['POST'])
def chat():
    if not API_KEY:
        return jsonify({"response": "GCP_API_KEY is missing from Vercel configuration variables."}), 500

    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"response": "Invalid prompt structure."}), 400
        
        user_message = data['message']
        knowledge_context = load_knowledge_base()
        merits_context = load_merits_data()

        system_instruction = (
            "You are the official University of Narowal Admissions AI assistant. "
            f"Context:\n{knowledge_context}\n\nMerits:\n{json.dumps(merits_context)}"
        )

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )

        response = model.generate_content(user_message)
        return jsonify({"response": response.text, "status": "success"})

    except Exception as e:
        return jsonify({"response": f"Runtime exception occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
