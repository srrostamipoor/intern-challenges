from flask import Flask, jsonify
import os

app = Flask(__name__)
DATA_FILE = "/data/visits.txt"

def read_count():
    os.makedirs("/data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        return 0
    with open(DATA_FILE) as f:
        return int(f.read().strip() or 0)

def write_count(n):
    with open(DATA_FILE, "w") as f:
        f.write(str(n))

@app.route("/")
def index():
    count = read_count() + 1
    write_count(count)
    return jsonify({"visits": count})

@app.route("/reset")
def reset():
    write_count(0)
    return jsonify({"visits": 0})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)