from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory storage of flagged posts (will reset on restart)
flagged_posts = []

@app.route("/")
def home():
    return "Misinformation Guard API is running."

@app.route("/flagged", methods=["GET"])
def get_flagged():
    return jsonify(flagged_posts)

@app.route("/add", methods=["POST"])
def add_flagged():
    data = request.json
    data['timestamp'] = datetime.utcnow().isoformat()
    flagged_posts.append(data)
    return jsonify({"status": "added"}), 201

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)