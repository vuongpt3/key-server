from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import uuid
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/create-key", methods=["POST"])
def create_key():
    data = request.json
    duration = data.get("duration")
    if duration not in [7, 30, 60]:
        return jsonify({"success": False, "message": "Chỉ chấp nhận 7, 30 hoặc 60 ngày"})

    code = uuid.uuid4().hex[:8].upper()
    key_str = f"VIP_{duration}D_{code}"

    keys = load_data()
    keys.append({
        "key": key_str,
        "duration": duration,
        "createdAt": datetime.utcnow().isoformat(),
        "deviceId": None
    })
    save_data(keys)

    return jsonify({"success": True, "key": key_str})

@app.route("/check-key", methods=["POST"])
def check_key():
    data = request.json
    key = data.get("key")
    device_id = data.get("deviceId")

    keys = load_data()
    for item in keys:
        if item["key"] == key:
            created = datetime.fromisoformat(item["createdAt"])
            if datetime.utcnow() > created + timedelta(days=item["duration"]):
                return jsonify({"success": False, "message": "Key đã hết hạn"})
            if item["deviceId"] is None:
                item["deviceId"] = device_id
                save_data(keys)
            elif item["deviceId"] != device_id:
                return jsonify({"success": False, "message": "Sai thiết bị"})
            return jsonify({"success": True, "message": "Key hợp lệ"})
    return jsonify({"success": False, "message": "Key không tồn tại"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)