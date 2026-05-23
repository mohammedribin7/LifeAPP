from flask import Flask, render_template, request, jsonify
import json, os
from datetime import date, datetime, timedelta

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

def default_data():
    return {
        "name": "",
        "water_goal": 8,
        "master_streak": 0,
        "last_full_day": "",
        "last_date": str(date.today()),
        "sleep": [],
        "water": 0,
        "steps": None,
        "spend_today": 0.0,
        "spend_log": [],
        "habits": [
            {"id": 1, "name": "Morning workout", "done": False, "streak": 0},
            {"id": 2, "name": "Read 20 mins",    "done": False, "streak": 0},
            {"id": 3, "name": "No sugar",         "done": False, "streak": 0},
            {"id": 4, "name": "Meditate",         "done": False, "streak": 0},
        ],
        "goals": [
            {"id": 1, "name": "Save $10,000", "current": 3200, "target": 10000, "unit": "$"},
            {"id": 2, "name": "Run a 5K",     "current": 3,    "target": 5,     "unit": "km"},
            {"id": 3, "name": "Read 12 books","current": 4,    "target": 12,    "unit": "books"},
        ],
    }

def load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    d = default_data()
    save(d)
    return d

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def day_reset(data):
    today = str(date.today())
    if data.get("last_date") == today:
        return data
    all_done = all(h["done"] for h in data["habits"])
    if all_done:
        data["master_streak"] = data.get("master_streak", 0) + 1
        data["last_full_day"] = data.get("last_date", "")
    else:
        data["master_streak"] = 0
    for h in data["habits"]:
        if h["done"]:
            h["streak"] = h.get("streak", 0) + 1
        else:
            h["streak"] = 0
        h["done"] = False
    data["water"] = 0
    data["steps"] = None
    data["spend_today"] = 0.0
    data["last_date"] = today
    save(data)
    return data

@app.route("/")
def index():
    data = day_reset(load())
    return render_template("index.html", data=data)

@app.route("/api/data")
def api_data():
    data = day_reset(load())
    return jsonify(data)

@app.route("/api/save", methods=["POST"])
def api_save():
    data = request.json
    save(data)
    return jsonify({"ok": True})

@app.route("/api/reset", methods=["POST"])
def api_reset():
    d = default_data()
    save(d)
    return jsonify(d)

if __name__ == "__main__":
    print("\n✅  Life Dashboard running!")
    print("📱  Open in your browser: http://localhost:8080\n")
    app.run(debug=False, host="0.0.0.0", port=8080)
