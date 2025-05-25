from flask import Flask, request, jsonify
import json
import uuid
import time
import os

app = Flask(__name__)
DATA_FILE = "keys.json"

def load_keys():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_keys(keys):
    with open(DATA_FILE, "w") as f:
        json.dump(keys, f, indent=2)

def generate_key(time_str):
    prefix = f"VIP_{time_str}_"
    random_part = uuid.uuid4().hex[:8]
    return prefix + random_part, int(time.time())

@app.route("/create-key", methods=["POST"])
def create_key():
    data = request.get_json()
    time_type = data.get("time_type")  # 2H, 5H, 1D, 7D, 14D, 30D, 60D
    device_limit = data.get("device_limit", 1)

    now = int(time.time())

    # Thời gian & giá tiền
    plan_info = {
        "2H": {"hours": 2, "price": "Free"},
        "5H": {"hours": 5, "price": "Free"},
        "1D": {"hours": 24, "price": "50k"},
        "7D": {"hours": 168, "price": "200k"},
        "14D": {"hours": 336, "price": "400k"},
        "30D": {"hours": 720, "price": "500k"},
        "60D": {"hours": 1440, "price": "700k"},
    }

    if time_type not in plan_info:
        return jsonify({"error": "Invalid time type"}), 400

    hours = plan_info[time_type]["hours"]
    price = plan_info[time_type]["price"]
    expire_time = now + hours * 3600

    key, created = generate_key(time_type)

    keys = load_keys()
    keys[key] = {
        "created": created,
        "expire": expire_time,
        "device_limit": device_limit,
        "devices": [],
        "price": price,
        "time_type": time_type
    }
    save_keys(keys)

    return jsonify({
        "key": key,
        "expire_time": expire_time,
        "price": price
    })

@app.route("/check-key", methods=["POST"])
def check_key():
    data = request.get_json()
    key = data.get("key")
    device_id = data.get("device_id")

    keys = load_keys()

    # Xóa key hết hạn quá 3 ngày
    now = int(time.time())
    expired_keys = [k for k, v in keys.items() if v["expire"] + 3*24*3600 < now]
    for k in expired_keys:
        del keys[k]
    save_keys(keys)

    if key not in keys:
        return jsonify({"valid": False, "reason": "Key not found or expired"})

    key_data = keys[key]
    if now > key_data["expire"]:
        return jsonify({"valid": False, "reason": "Key expired"})

    if device_id not in key_data["devices"]:
        if len(key_data["devices"]) >= key_data["device_limit"]:
            return jsonify({"valid": False, "reason": "Device limit reached"})
        key_data["devices"].append(device_id)
        save_keys(keys)

    return jsonify({
        "valid": True,
        "expire": key_data["expire"],
        "price": key_data["price"],
        "time_type": key_data["time_type"],
        "used_devices": len(key_data["devices"]),
        "device_limit": key_data["device_limit"]
    })

@app.route("/", methods=["GET"])
def index():
    return "Key Server is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)