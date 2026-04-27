from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
import sqlite3
import time

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        filename TEXT,
        timestamp REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME (LOGIN) ----------------
@app.route("/")
def home():
    return render_template("login.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    if username == "admin" and password == "1234":
        session["user"] = username
        return redirect("/dashboard")

    return "Invalid Login ❌"

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""
        SELECT filename, message FROM posts
        WHERE username=?
        ORDER BY id DESC
    """, (session["user"],))

    posts = c.fetchall()
    conn.close()

    return render_template("dashboard.html", posts=posts)

# ---------------- UPLOAD (TEXT + IMAGE) ----------------
@app.route("/upload", methods=["POST"])
def upload():
    if "user" not in session:
        return redirect("/")

    file = request.files["file"]
    message = request.form["message"]

    filename = str(int(time.time())) + "_" + file.filename
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO posts (username, message, filename, timestamp)
        VALUES (?, ?, ?, ?)
    """, (session["user"], message, filename, time.time()))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- DOWNLOAD ----------------
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# ---------------- RUN (RENDER FIX) ----------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
