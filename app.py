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

            GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"
            gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()

            if not gemini_key:
                return jsonify({"reply": "Error: GEMINI_API_KEY is not set on the server.", "is_image": False}), 500

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": gemini_key
            }

            payload = {
                "contents": [
                    {"parts": [{"text": clean_prompt}]}
                ],
                "generationConfig": {
                    "responseModalities": ["IMAGE"]
                }
            }

            response = requests.post(GEMINI_API_URL, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                # The image is buried inside candidates -> content -> parts -> inlineData -> data
                parts = result["candidates"][0]["content"]["parts"]
                image_part = next((p for p in parts if "inlineData" in p), None)

                if image_part:
                    base64_image = image_part["inlineData"]["data"]
                    mime_type = image_part["inlineData"].get("mimeType", "image/png")
                    image_data_url = f"data:{mime_type};base64,{base64_image}"
                    return jsonify({"reply": image_data_url, "is_image": True})
                else:
                    return jsonify({"reply": "Image gen failed: no image data in Gemini response", "is_image": False})
            else:
                return jsonify({"reply": f"Image gen failed: {response.status_code} {response.text}", "is_image": False})

        except Exception as e:
            return jsonify({"reply": f"Image Generation Error: {str(e)}"}), 500

    else:
        try:
            if client is None:
                return jsonify({"reply": "Error: GROQ_API_KEY is not set on the server.", "is_image": False}), 500

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=chat_history,
                temperature=0.7,
            )
            reply_text = completion.choices[0].message.content
            return jsonify({"reply": reply_text, "is_image": False})

        except Exception as e:
            return jsonify({"reply": f"Chat Error: {str(e)}", "is_image": False}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
