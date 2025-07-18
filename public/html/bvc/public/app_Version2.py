from flask import Flask, request, jsonify
from flask_cors import CORS
import mariadb
import hashlib
import bcrypt

app = Flask(__name__)
CORS(app)

def get_db():
    return mariadb.connect(
        user="mefaloo",
        password="010101",
        host="localhost",
        database="vibecode"
    )

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    if not username or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, password_hash))
        conn.commit()
        return jsonify({"success": True})
    except mariadb.IntegrityError:
        return jsonify({"error": "Username or email already exists"}), 400
    finally:
        cur.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash FROM users WHERE username=? OR email=? LIMIT 1", (username, username))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row and bcrypt.checkpw(password.encode(), row[2].encode()):
        return jsonify({"success": True, "user": row[1]})
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/api/posts', methods=['GET'])
def get_posts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT posts.id, posts.title, posts.content, users.username as author, posts.created_at
        FROM posts
        JOIN users ON posts.author_id = users.id
        ORDER BY posts.created_at DESC
    """)
    posts = [
        {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "author": row[3],
            "created_at": str(row[4])
        }
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return jsonify(posts)

@app.route('/api/create_post', methods=['POST'])
def create_post():
    data = request.get_json()
    title = data.get("title")
    content = data.get("content")
    author = data.get("author")
    if not title or not content or not author:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=? LIMIT 1", (author,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        return jsonify({"error": "Invalid user"}), 401

    author_id = user[0]
    cur.execute("INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)", (title, content, author_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)