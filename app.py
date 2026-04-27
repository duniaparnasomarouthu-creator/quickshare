from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
import sqlite3
import time

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DB setup
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            user TEXT,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# LOGIN PAGE
@app.route("/")
def home():
    return render_template("login.html")

# LOGIN CHECK
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    if username == "admin" and password == "1234":
        session["user"] = username
        return redirect("/dashboard")
    return "Invalid login"

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT filename FROM images WHERE user=?", (session["user"],))
    images = c.fetchall()
    conn.close()

    return render_template("dashboard.html", images=images)

# UPLOAD
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]

    filename = str(int(time.time())) + "_" + file.filename
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("INSERT INTO images (filename, user, timestamp) VALUES (?, ?, ?)",
              (filename, session["user"], time.time()))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# DOWNLOAD
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
