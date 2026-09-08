from dotenv import load_dotenv
load_dotenv() # This looks for your .env file automatically
from flask import Flask, request, jsonify, send_from_directory
from groq import Groq
import os

app = Flask(__name__)

# Securely read your Groq Key from your Mac's environment
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


import os

@app.route('/')
def home():
    # Automatically calculates the exact absolute directory path of app.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(base_dir, 'index.html')


import urllib.parse  # Built into Python to safely format URL strings

import urllib.parse

@app.route('/api/chat', methods=['POST'])
def chat():
    user_data = request.json
    chat_history = user_data.get("messages", [])
    
    # Grab the last text message typed by the user
    last_user_message = chat_history[-1]["content"] if chat_history else ""
    msg_lower = last_user_message.lower()

    # Check if the user is requesting an image
    keywords = ["generate an image of", "generate image of", "generate an image", "generate image", "create an image of", "create an image", "picture of", "draw a", "draw"]
    if any(kw in msg_lower for kw in keywords):
        try:
            # Clean up the prompt by dynamically removing the matched keyword
            clean_prompt = msg_lower
            for kw in keywords:
                if kw in clean_prompt:
                    clean_prompt = clean_prompt.replace(kw, "", 1) # Only remove the first instance
            
            clean_prompt = clean_prompt.strip()
            
            # Fallback if the user just typed "draw" without describing anything
            if not clean_prompt:
                clean_prompt = "a beautiful random digital painting art"
            
            # Encodes text spaces safely for a URL
            encoded_prompt = urllib.parse.quote(clean_prompt)
            
            # Updated Pollinations endpoint using modern model mapping
            image_url = f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&nologo=true&seed=42"
            
            return jsonify({"reply": image_url, "is_image": True})
            
        except Exception as e:
            return jsonify({"reply": f"Image Generation Error: {str(e)}"}), 500

    # Otherwise, pass regular text directly to Groq like normal
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b", 
            messages=chat_history
        )
        bot_reply = completion.choices.message.content
        return jsonify({"reply": bot_reply, "is_image": False})
    except Exception as e:
        return jsonify({"reply": f"Backend Error: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)