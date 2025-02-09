from flask import Flask, render_template, request, jsonify
import requests
import json
import os

app = Flask(__name__, template_folder="templates", static_folder="static")

# DeepSeek API的URL和你的API密钥
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat"
API_KEY = "sk-337a57fd70074fb39703ebc81174e6cd"

# 确保data目录存在
if not os.path.exists("data"):
    os.makedirs("data")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods="POST")
def chat():
    user_message = request.json.get("message")
    conversation_id = request.json.get("conversation_id")

    # 调用DeepSeek API
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {"message": user_message}
    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        bot_message = response.json().get("response")

        # 保存对话内容
        save_conversation(conversation_id, user_message, bot_message)

        return jsonify({"message": bot_message})
    else:
        return jsonify({"error": "Failed to get response from DeepSeek API"}), 500


def save_conversation(conversation_id, user_message, bot_message):
    conversation_file = f"data/conversations.json"

    if os.path.exists(conversation_file):
        with open(conversation_file, "r") as f:
            conversations = json.load(f)
    else:
        conversations = {}

    if conversation_id not in conversations:
        conversations.conversation_id = None

    conversations.conversation_id.append({"user": user_message, "bot": bot_message})

    with open(conversation_file, "w") as f:
        json.dump(conversations, f)


if __name__ == "__main__":
    app.run(debug=True)
