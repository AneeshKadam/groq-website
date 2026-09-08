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


@app.route('/api/chat', methods=['POST'])
def chat():
    user_data = request.json
    # 1. Grab the entire history array sent from the website
    chat_history = user_data.get("messages", [])

    try:
        # 2. Feed the entire history array directly into Groq
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_history
        )
        bot_reply = completion.choices[0].message.content
        return jsonify({"reply": bot_reply})
    except Exception as e:
        return jsonify({"reply": f"Backend Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
