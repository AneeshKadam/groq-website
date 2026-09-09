import os
import requests
import base64
import urllib.parse
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from groq import Groq

app = Flask(__name__)
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# Securely pulls the Hugging Face token from Render
HF_TOKEN = os.getenv("HF_TOKEN")

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

            # Premium Free Model: FLUX.1 (Way better than basic options)
            API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            
            # Request raw image bytes from Hugging Face
            response = requests.post(API_URL, headers=headers, json={"inputs": clean_prompt})
            
            if response.status_code == 200:
                # Convert the raw image bytes into a safe Base64 string for HTML
                base64_image = base64.b64encode(response.content).decode('utf-8')
                image_data_url = f"data:image/jpeg;base64,{base64_image}"
                return jsonify({"reply": image_data_url, "is_image": True})
            else:
                return jsonify({"reply": f"Hugging Face API Error: {response.text}", "is_image": False})
                
        except Exception as e:
            return jsonify({"reply": f"Image Generation Error: {str(e)}"}), 500

    # Otherwise, pass regular text directly to Groq
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b", 
            messages=chat_history
        )
        bot_reply = completion.choices.message.content
        return jsonify({"reply": bot_reply, "is_image": False})
    except Exception as e:
        return jsonify({"reply": f"Backend Error: {str(e)}"}), 500
