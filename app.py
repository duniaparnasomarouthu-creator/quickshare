from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
import time
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- ADMIN ----------------
ADMIN_USER = "admin"
ADMIN_PASS = "1234"

# ---------------- DATABASE CONNECTION ----------------
def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])

# ---------------- INIT DB ----------------
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
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
        id SERIAL PRIMARY KEY,
        username TEXT,
        message TEXT,
        filename TEXT,
        timestamp FLOAT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        id SERIAL PRIMARY KEY,
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

        conn = get_db()
        c = conn.cursor()

        try:
            c.execute("""
            INSERT INTO users (username, password, email, age, dob, gender)
            VALUES (%s, %s, %s, %s, %s, %s)
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
    if username == ADMIN_USER and password == ADMIN_PASS:
        session["user"] = username
        session["admin"] = True
        return redirect("/admin")

    # USER LOGIN
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE username=%s", (username,))
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

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    SELECT filename, message FROM posts
    WHERE username=%s
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

    filename = str(int(time.time())) + "_" + file.filename
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    INSERT INTO posts (username, message, filename, timestamp)
    VALUES (%s, %s, %s, %s)
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

    conn = get_db()
    c = conn.cursor()

    c.execute("INSERT INTO ratings (username, rating) VALUES (%s, %s)",
              (session["user"], rating))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return "Access Denied ❌"

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    c.execute("SELECT AVG(rating) FROM ratings")
    avg_rating = c.fetchone()[0] or 0

    c.execute("SELECT username, email, age, gender FROM users")
    users = c.fetchall()

    c.execute("SELECT username, rating FROM ratings")
    ratings = c.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        total_users=total_users,
        avg_rating=avg_rating,
        users=users,
        ratings=ratings
    )

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN (IMPORTANT FOR RENDER) ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
