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

@app.route('/api/chat', methods=['POST'])
def chat():
    user_data = request.json
    chat_history = user_data.get("messages", [])
    
    # Grab the last text message typed by the user
    last_user_message = chat_history[-1]["content"].lower() if chat_history else ""

    # Check if the user is requesting an image
    if any(keyword in last_user_message for keyword in ["generate an image", "generate image", "draw", "create an image", "picture of"]):
        try:
            # Clean up the prompt to use as an image description
            clean_prompt = last_user_message.replace("generate an image of", "").replace("generate image of", "").replace("draw a", "").replace("draw", "").strip()
            
            # Encodes text spaces for a URL (e.g., "red car" becomes "red%20car")
            encoded_prompt = urllib.parse.quote(clean_prompt)
            
            # Using Pollinations.ai (a completely free, no-key text-to-image API)
            image_url = f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&nologo=true"
            
            # Return a special flag so the frontend knows to display an image block
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