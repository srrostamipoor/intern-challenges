from flask import Flask, jsonify
import redis

app = Flask(__name__)
# Docker's built-in DNS resolves "redis" to the redis container's IP
r = redis.Redis(host="redis", port=6379, decode_responses=True)

@app.route("/")
def index():
    count = r.incr("visits")
    return jsonify({"visits": count, "from": "api"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)