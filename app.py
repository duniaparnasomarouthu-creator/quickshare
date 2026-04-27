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
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        filename TEXT,
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
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        email = request.form["email"]
        age = request.form["age"]
        dob = request.form["dob"]
        gender = request.form["gender"]

        conn = sqlite3.connect("data.db")
        c = conn.cursor()

        try:
            c.execute("""
            INSERT INTO users (username, password, email, age, dob, gender)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (username, password, email, age, dob, gender))
            conn.commit()
        except:
            return "User already exists ❌"

        conn.close()
        return redirect("/")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    # ADMIN LOGIN
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

# ---------------- UPLOAD ----------------
@app.route("/upload", methods=["POST"])
def upload():
    if "user" not in session:
        return redirect("/")

    file = request.files["file"]
    message = request.form["message"]

    filename = ""

    if file and file.filename != "":
        filename = str(int(time.time())) + "_" + file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))

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

# ---------------- RATE ----------------
@app.route("/rate", methods=["POST"])
def rate():
    if "user" not in session:
        return redirect("/")

    rating = request.form["rating"]

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("INSERT INTO ratings (username, rating) VALUES (?, ?)",
              (session["user"], rating))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return "Access Denied ❌"

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # TOTAL USERS
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    # ALL USERS
    c.execute("SELECT username, email, age, gender FROM users")
    users = c.fetchall()

    # ALL RATINGS (OLD + NEW)
    c.execute("SELECT username, rating FROM ratings")
    ratings = c.fetchall()

    # AVERAGE RATING
    c.execute("SELECT AVG(rating) FROM ratings")
    avg_rating = c.fetchone()[0] or 0

    # TOTAL RATINGS COUNT
    c.execute("SELECT COUNT(*) FROM ratings")
    total_ratings = c.fetchone()[0]

    # PERCENTAGE
    rating_percent = (avg_rating / 5) * 100 if total_ratings > 0 else 0

    # COUNT EACH RATING
    c.execute("SELECT rating, COUNT(*) FROM ratings GROUP BY rating")
    rating_counts = c.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        total_users=total_users,
        users=users,
        ratings=ratings,
        avg_rating=round(avg_rating, 2),
        rating_percent=round(rating_percent, 2),
        rating_counts=rating_counts
    )

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
