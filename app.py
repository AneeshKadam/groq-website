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
    user_data = request.get_json(silent=True) or {}
    chat_history = user_data.get("messages", [])

    if not isinstance(chat_history, list) or not chat_history:
        return jsonify({"reply": "Please send a message and try again.", "is_image": False}), 400

    if not all(isinstance(message, dict) and message.get("role") in ("user", "assistant", "system") and isinstance(message.get("content"), str) for message in chat_history):
        return jsonify({"reply": "The chat history format is invalid.", "is_image": False}), 400

    last_user_message = next((message["content"] for message in reversed(chat_history) if message.get("role") == "user"), "")
    msg_lower = last_user_message.lower()

    image_intent = (
        re.search(r"\b(generate|create|make)\b.{0,60}\b(image|picture|photo|illustration|artwork)\b", last_user_message, re.I)
        or re.search(r"\b(draw|paint)\b(?:\s+me)?\s+(?:an?\s+)?", last_user_message, re.I)
        or re.search(r"\b(picture|image|photo)\s+of\b", last_user_message, re.I)
    )
    if image_intent:
        try:
            # Keep the user's original capitalization and wording in the prompt.
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
                    return jsonify({"reply": image_data_url, "is_image": True})

            app.logger.error("Cloudflare image generation failed with status %s", response.status_code)
            return jsonify({
                "reply": "Image generation failed. Check the Cloudflare API settings and server logs, then try again.",
                "is_image": False
            }), 502

        except Exception:
            app.logger.exception("Cloudflare image generation request failed")
            return jsonify({
                "reply": "Image generation failed. Check that the Cloudflare account ID and API token are correct and that the token has permission to run Workers AI models.",
                "is_image": False
            }), 502

    else:
        try:
            if client is None:
                return jsonify({"reply": "Error: GROQ_API_KEY is not set on the server.", "is_image": False}), 500

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=chat_history,
                temperature=0.7,
            )
            reply_text = completion.choices[0].message.content or ""
            if not reply_text:
                return jsonify({"reply": "The AI returned an empty response. Please try again.", "is_image": False}), 502
            return jsonify({"reply": reply_text, "is_image": False})

        except Exception:
            app.logger.exception("Groq chat request failed")
            return jsonify({
                "reply": "Chat failed. Check the server logs and API configuration, then try again.",
                "is_image": False
            }), 502


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
