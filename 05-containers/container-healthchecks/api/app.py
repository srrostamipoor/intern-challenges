from flask import Flask, jsonify
import time

app = Flask(__name__)
_healthy = True
_start_time = time.monotonic()


@app.route("/health")
def health():
    if not _healthy:
        return jsonify({"status": "down", "reason": "simulated failure"}), 503
    uptime = time.monotonic() - _start_time
    return jsonify({"status": "ok", "uptime_seconds": round(uptime, 1)}), 200


@app.route("/break")
def break_health():
    global _healthy
    _healthy = False
    return jsonify({"status": "health check will now fail"})


@app.route("/fix")
def fix_health():
    global _healthy
    _healthy = True
    return jsonify({"status": "health check restored"})


@app.route("/")
def index():
    return jsonify({"message": "api is running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)