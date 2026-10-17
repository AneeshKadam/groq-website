import os
import re
import base64
import json
import requests
from flask import Flask, request, jsonify, send_from_directory, Response
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
    user_data = request.get_json(silent=True) or {}
    chat_history = user_data.get("messages", [])

    if not isinstance(chat_history, list) or not chat_history:
        return jsonify({"reply": "Please send a message and try again.", "is_image": False}), 400

    if not all(isinstance(message, dict) and message.get("role") in ("user", "assistant", "system") and isinstance(message.get("content"), str) for message in chat_history):
        return jsonify({"reply": "The chat history format is invalid.", "is_image": False}), 400

    last_user_message = next((message["content"] for message in reversed(chat_history) if message.get("role") == "user"), "")

    image_intent = (
        re.search(r"\b(generate|create|make)\b.{0,60}\b(image|picture|photo|illustration|artwork)\b", last_user_message, re.I)
        or re.search(r"\b(draw|paint)\b(?:\s+me)?\s+(?:an?\s+)?", last_user_message, re.I)
        or re.search(r"\b(picture|image|photo)\s+of\b", last_user_message, re.I)
    )
    
    if image_intent:
        try:
            clean_prompt = re.sub(
                r"^\s*(please\s+)?(generate|create|make)\s+(me\s+)?(an?\s+)?(image|picture|photo|illustration|artwork)\s*(of)?\s*",
                "",
                last_user_message,
                flags=re.I,
            )
            clean_prompt = re.sub(
                r"^\s*(please\s+)?(draw|paint)\s+(me\s+)?(an?\s+)?",
                "",
                clean_prompt,
                flags=re.I,
            ).strip(" \t\n.,!?")

            if not clean_prompt:
                clean_prompt = "cinematic digital painting artwork, highly detailed"

            account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
            cf_token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()

            if not account_id or not cf_token:
                return jsonify({"reply": "Error: CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN is not set on the server.", "is_image": False}), 500

            CF_API_URL = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"

            headers = {
                "Authorization": f"Bearer {cf_token}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                CF_API_URL,
                headers=headers,
                json={"prompt": clean_prompt},
                timeout=90,
            )

            if response.ok:
                result = response.json()
                base64_image = result.get("result", {}).get("image")
                if base64_image:
                    image_data_url = f"data:image/jpeg;base64,{base64_image}"
                    # Wrap image inside a small text signature so the frontend knows it is a JSON package
                    return jsonify({"reply": image_data_url, "is_image": True})

            app.logger.error("Cloudflare image generation failed with status %s", response.status_code)
            return jsonify({
                "reply": "Image generation failed. Check the Cloudflare API settings and server logs, then try again.",
                "is_image": False
            }), 502

        except Exception:
            app.logger.exception("Cloudflare image generation request failed")
            return jsonify({
                "reply": "Image generation failed. Check details on server configuration logs.",
                "is_image": False
            }), 502

    else:
        # --- STREAMING CHAT COMPLETION ---
        if client is None:
            return jsonify({"reply": "Error: GROQ_API_KEY is not set on the server.", "is_image": False}), 500

        try:
            def generate_stream():
                system_message = {
                    "role": "system",
                    "content": "Answer in plain, simple language. Start with the direct answer. Keep replies under 100 words unless the user asks for more detail."
                }
            
                messages = [system_message] + [
                    message for message in chat_history
                    if message.get("role") != "system"
                ]
            
                completion = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=250,
                    stream=True
                )
            
                for chunk in completion:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        return Response(generate_stream(), mimetype='text/plain')

        except Exception:
            app.logger.exception("Groq chat streaming request failed")
            return jsonify({
                "reply": "Chat failed. Check the server logs and API configuration, then try again.",
                "is_image": False
            }), 502


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

