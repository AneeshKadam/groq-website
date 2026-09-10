import os
import base64
import requests
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from groq import Groq

app = Flask(__name__)
load_dotenv()

# Do not prevent the Flask app from starting when the optional Groq key is absent.
groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
client = Groq(api_key=groq_api_key) if groq_api_key else None

@app.route('/')
def home():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(base_dir, 'index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    user_data = request.json
    chat_history = user_data.get("messages", [])
    
    last_user_message = chat_history[-1]["content"] if chat_history else ""
    msg_lower = last_user_message.lower()

    keywords = ["generate an image of", "generate image of", "generate an image", "generate image", "create an image of", "create an image", "picture of", "draw a", "draw"]
    if any(kw in msg_lower for kw in keywords):
        try:
            clean_prompt = msg_lower
            for kw in keywords:
                clean_prompt = clean_prompt.replace(kw, "", 1)
            clean_prompt = clean_prompt.strip()

            if not clean_prompt:
                clean_prompt = "cinematic digital painting artwork, highly detailed"

            API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
            token = os.environ.get("HF_TOKEN", "").strip()
            headers = {
                "Authorization": f"Bearer {token}"
            }

            response = requests.post(
                API_URL,
                headers=headers,
                json={"inputs": clean_prompt}
            )

            if response.status_code == 200:
                base64_image = base64.b64encode(response.content).decode('utf-8')
                image_data_url = f"data:image/jpeg;base64,{base64_image}"
                return jsonify({"reply": image_data_url, "is_image": True})
            else:
                return jsonify({"reply": f"Image gen failed: {response.status_code} {response.text}", "is_image": False})

        except Exception as e:
            return jsonify({"reply": f"Image Generation Error: {str(e)}"}), 500
