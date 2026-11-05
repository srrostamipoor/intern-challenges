from flask import Flask, request, jsonify
import os, psycopg2, redis

app = Flask(__name__)


def read_secret(name):
    """Read a Docker secret from /run/secrets/<name>, fall back to env var."""
    secret_path = f"/run/secrets/{name}"
    if os.path.exists(secret_path):
        with open(secret_path) as f:
            return f.read().strip()
    return os.getenv(name.upper(), "")


DB_PASSWORD = read_secret("db_password")


def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        dbname=os.getenv("DB_NAME", "appdb"),
        user=os.getenv("DB_USER", "appuser"),
        password=DB_PASSWORD,
    )


r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), decode_responses=True)

@app.before_request
def init_db():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, text TEXT)")
    conn.commit()
    conn.close()

@app.route("/messages", methods=["GET"])
def get_messages():
    cached = r.get("messages")
    if cached:
        return jsonify({"source": "cache", "messages": cached.split("|")})
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT text FROM messages ORDER BY id")
        rows = [row[0] for row in cur.fetchall()]
    conn.close()
    r.setex("messages", 30, "|".join(rows))
    return jsonify({"source": "db", "messages": rows})

@app.route("/messages", methods=["POST"])
def add_message():
    text = request.json.get("text", "")
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO messages (text) VALUES (%s)", (text,))
    conn.commit()
    conn.close()
    r.delete("messages")   # invalidate cache
    return jsonify({"added": text}), 201

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)