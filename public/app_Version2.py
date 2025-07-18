from flask import Flask, request, jsonify, session
from flask_cors import CORS
import mariadb
import bcrypt

app = Flask(__name__)

# Only allow your frontend origin and support credentials (cookies)
CORS(app, supports_credentials=True, origins=["http://localhost:8000"])
app.secret_key = 'czPHxO$z##W7je!3hdiBD28dfIB8zIQ'  # Change to a strong random value in production!

# ---- HTTP SESSION COOKIE SUPPORT ----
# Ensure the session cookie works over HTTP during development!
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
# -------------------------------------

def get_db():
    return mariadb.connect(
        user="mefaloo",
        password="010101",
        host="localhost",
        database="vibecode"
    )

# --- BEGIN CORS OPTIONS ROUTE DEBUGGING FIX ---

# WORKAROUND: Print all registered routes and their allowed methods at startup for debugging
if __name__ == '__main__':
    print("=== Flask Registered Routes and Methods ===")
    # Temporary app for route printing before app.run
    # (app.url_map is populated after all routes are created)
    for rule in app.url_map.iter_rules():
        print(f"{rule} {rule.methods}")
    print("==========================================")

# Global handler for OPTIONS requests if a route is missing OPTIONS
@app.errorhandler(404)
def handle_404(e):
    # Special workaround: if this was an OPTIONS preflight, log it
    if request.method == "OPTIONS":
        print(f"WARNING: Received OPTIONS for {request.path} but no matching route with OPTIONS method.")
        # Optionally, return CORS headers (not usually needed if Flask-CORS is set up)
        resp = app.make_response(jsonify(success=True), 204)
        resp.headers["Access-Control-Allow-Origin"] = "http://localhost:8000"
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    return e

# --- END CORS OPTIONS ROUTE DEBUGGING FIX ---

# --- TROUBLESHOOTING STEPS ---
@app.route('/api/troubleshooting/cors', methods=['GET', 'OPTIONS'])
def troubleshoot_cors():
    """
    Test endpoint to verify CORS headers and session.
    Use this from your browser/devtools or curl to check CORS headers,
    session handling, and response format.
    """
    origin = request.headers.get('Origin')
    test_session_value = session.get('test_session', None)
    session['test_session'] = 'active'
    return jsonify({
        "message": "CORS and session troubleshooting endpoint.",
        "origin_header": origin,
        "access_control_allow_origin": request.headers.get('Access-Control-Allow-Origin'),
        "session_value": test_session_value,
        "session_now": session.get('test_session'),
        "cookies": request.cookies
    })

@app.after_request
def after_request(response):
    # Print CORS and session headers for debugging purposes
    print("---- Flask After Request Headers ----")
    print(dict(response.headers))
    print("Session contents:", dict(session))
    print("-------------------------------------")
    return response
# --- END TROUBLESHOOTING STEPS ---

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
    # Allow login with either username or email
    cur.execute("SELECT id, username, password_hash FROM users WHERE username=? OR email=? LIMIT 1", (username, username))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row and bcrypt.checkpw(password.encode(), row[2].encode()):
        session['username'] = row[1]  # Set the session cookie
        session['user_id'] = row[0]
        return jsonify({"success": True, "user": row[1]})
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/api/check_session', methods=['GET'])
def check_session():
    if 'username' in session:
        return jsonify({"logged_in": True, "username": session['username']})
    else:
        return jsonify({"logged_in": False})

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
    return jsonify({"posts": posts})  # <--- FIXED: returns posts in a 'posts' key

@app.route('/api/create_post', methods=['POST', 'OPTIONS'])
def create_post():
    # Handle CORS preflight OPTIONS request first, return JSON!
    if request.method == 'OPTIONS':
        return jsonify(success=True), 204

    if 'username' not in session or 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    title = data.get("title")
    content = data.get("content")
    if not title or not content:
        return jsonify({"error": "Missing fields"}), 400

    author_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)", (title, content, author_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)