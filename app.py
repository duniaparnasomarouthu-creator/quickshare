from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os
import time
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        age INTEGER,
        dob TEXT,
        gender TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        folder_name TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        filename TEXT,
        folder TEXT,
        size INTEGER,
        timestamp REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        rating INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = sqlite3.connect("data.db")
        c = conn.cursor()

        try:
            c.execute("""
            INSERT INTO users (username,password,email,age,dob,gender)
            VALUES (?,?,?,?,?,?)
            """, (
                request.form["username"],
                generate_password_hash(request.form["password"]),
                request.form["email"],
                request.form["age"],
                request.form["dob"],
                request.form["gender"]
            ))
            conn.commit()
        except:
            return "User exists ❌"

        conn.close()
        return redirect("/")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    if username == "admin" and password == "1234":
        session["user"] = username
        session["admin"] = True
        return redirect("/admin")

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user[0], password):
        session["user"] = username
        session["admin"] = False
        return redirect("/dashboard")

    return "Invalid ❌"

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT folder_name FROM folders WHERE username=?", (session["user"],))
    folders = c.fetchall()

    c.execute("""
    SELECT filename, message, folder FROM posts
    WHERE username=? ORDER BY id DESC
    """, (session["user"],))
    posts = c.fetchall()

    c.execute("SELECT SUM(size) FROM posts WHERE username=?", (session["user"],))
    total = c.fetchone()[0] or 0
    storage_mb = round(total/(1024*1024),2)

    conn.close()

    return render_template("dashboard.html", posts=posts, folders=folders, storage_mb=storage_mb)

# ---------------- CREATE FOLDER ----------------
@app.route("/create_folder", methods=["POST"])
def create_folder():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("INSERT INTO folders (username, folder_name) VALUES (?,?)",
              (session["user"], request.form["folder"]))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- UPLOAD ----------------
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    message = request.form["message"]
    folder = request.form["folder"]

    filename = ""
    size = 0

    if file and file.filename != "":
        filename = str(int(time.time())) + "_" + file.filename
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        size = os.path.getsize(path)

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""
    INSERT INTO posts (username,message,filename,folder,size,timestamp)
    VALUES (?,?,?,?,?,?)
    """, (session["user"], message, filename, folder, size, time.time()))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- RATE ----------------
@app.route("/rate", methods=["POST"])
def rate():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("INSERT INTO ratings (username,rating) VALUES (?,?)",
              (session["user"], request.form["rating"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return "Denied ❌"

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    c.execute("SELECT AVG(rating) FROM ratings")
    avg = c.fetchone()[0] or 0

    c.execute("SELECT username,email FROM users")
    users = c.fetchall()

    conn.close()

    return render_template("admin.html", total_users=total_users, avg=round(avg,2), users=users)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
