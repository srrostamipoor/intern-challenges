from flask import Flask, jsonify

app = Flask(__name__)


def add(a, b):
    return a + b


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
    
# touch to trigger a new run
# touch 2
