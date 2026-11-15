import os

from flask import Flask, jsonify

app = Flask(__name__)


def add(a, b):
    return a + b


@app.route("/")
def index():
    return jsonify({"status": "ok", "env": os.environ.get("APP_ENV", "dev")})


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/add/<int:a>/<int:b>")
def add_route(a, b):
    return jsonify({"result": add(a, b)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
