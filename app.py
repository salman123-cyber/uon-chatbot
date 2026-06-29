import os
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__, template_folder='templates')
CORS(app)

application = app

# Initialize Google AI
API_KEY = os.environ.get("GCP_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "uon_knowledge.txt")
MERITS_PATH = os.path.join(BASE_DIR, "merits_data_normalized.json")

# --- OPTIMIZATION: LOAD DATA INTO MEMORY ONCE ON STARTUP ---
def pre_load_context():
    content = ""
    if os.path.exists(KNOWLEDGE_PATH):
        try:
            with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
                content += f"--- UON ADMISSION INFORMATION ---\n{f.read()}\n\n"
        except Exception:
            pass
            
    if os.path.exists(MERITS_PATH):
        try:
            with open(MERITS_PATH, "r", encoding="utf-8") as f:
                json_data = json.load(f)
                content += f"--- PREVIOUS CLOSING MERITS DATA ---\n{json.dumps(json_data)}"
        except Exception:
            pass
            
    return content if content else "Default UON Admissions Context Data."

# Global context cache
STATIC_CONTEXT_CACHE = pre_load_context()


@app.route('/', methods=['GET'])
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Template Configuration Mismatch: {str(e)}"


@app.route('/api/chat', methods=['POST'])
def chat():
    if not API_KEY:
        return jsonify({"response": "Backend Missing Variable: GCP_API_KEY is not configured on Vercel Dashboard."}), 500

    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"response": "Invalid request message payload."}), 400
        
        user_message = data['message']

        # Use the ultra-fast global memory string instead of reading disk files over and over
        system_instruction = (
            "You are the official University of Narowal (UON) Admissions AI Assistant. "
            "Help students with accurate info about criteria, merits, programs, and fees using this context:\n\n"
            f"{STATIC_CONTEXT_CACHE}\n\n"
            "Keep answers concise, direct, and professional. If unknown, point to the registrar window."
        )

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )

        # Generate response from Gemini
        response = model.generate_content(user_message)
        
        # Check if response came back empty
        reply_text = response.text if response.text else "I am processing your query, please try rephrasing."

        return jsonify({
            "response": reply_text,
            "status": "success"
        })

    except Exception as e:
        # Fallback messaging so the frontend widget doesn't stay blank on a crash
        return jsonify({
            "response": f"The AI engine took too long or encountered an error: {str(e)}",
            "status": "error"
        }), 200  # Return 200 so the frontend catch block doesn't hide the error message
