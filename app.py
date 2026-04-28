from flask import Flask, render_template, request, redirect, session
import sqlite3, os, time
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------- DB (SAFE UPDATE, KEEP OLD DATA) --------
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # ADD columns safely (won't delete old data)
    try:
        c.execute("ALTER TABLE posts ADD COLUMN folder TEXT DEFAULT 'root'")
    except:
        pass

    try:
        c.execute("ALTER TABLE posts ADD COLUMN size INTEGER DEFAULT 0")
    except:
        pass

    c.execute("""
    CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        folder_name TEXT
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

# -------- HOME --------
@app.route("/")
def home():
    return render_template("login.html")

# -------- LOGIN --------
@app.route("/login", methods=["POST"])
def login():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE username=?", (request.form["username"],))
    user = c.fetchone()

    if user and check_password_hash(user[0], request.form["password"]):
        session["user"] = request.form["username"]
        return redirect("/dashboard")

    return "Invalid login ❌"

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------- DASHBOARD --------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    current_folder = request.args.get("folder", "root")

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT folder_name FROM folders WHERE username=?", (session["user"],))
    folders = c.fetchall()

    c.execute("""
    SELECT filename, message, COALESCE(folder,'root')
    FROM posts
    WHERE username=? AND (folder=? OR folder IS NULL)
    """, (session["user"], current_folder))
    posts = c.fetchall()

    conn.close()

    return render_template("dashboard.html",
                           folders=folders,
                           posts=posts,
                           current_folder=current_folder)

# -------- CREATE FOLDER --------
@app.route("/create_folder", methods=["POST"])
def create_folder():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("INSERT INTO folders VALUES(NULL,?,?)",
              (session["user"], request.form["folder"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# -------- DELETE FOLDER --------
@app.route("/delete_folder/<name>")
def delete_folder(name):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("DELETE FROM folders WHERE folder_name=? AND username=?",
              (name, session["user"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# -------- RENAME FOLDER --------
@app.route("/rename_folder", methods=["POST"])
def rename():
    old = request.form["old"]
    new = request.form["new"]

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("UPDATE folders SET folder_name=? WHERE folder_name=? AND username=?",
              (new, old, session["user"]))

    c.execute("UPDATE posts SET folder=? WHERE folder=? AND username=?",
              (new, old, session["user"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# -------- UPLOAD --------
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    message = request.form["message"]
    folder = request.form["folder"]

    filename = ""

    if file and file.filename:
        filename = str(int(time.time())) + "_" + file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("INSERT INTO posts VALUES(NULL,?,?,?,?,?,?)",
              (session["user"], message, filename, folder, 0, time.time()))

    conn.commit()
    conn.close()

    return redirect(f"/dashboard?folder={folder}")

# -------- RATE --------
@app.route("/rate", methods=["POST"])
def rate():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("INSERT INTO ratings VALUES(NULL,?,?)",
              (session["user"], request.form["rating"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# -------- ADMIN --------
@app.route("/admin")
def admin():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT username FROM users")
    users = c.fetchall()

    c.execute("SELECT username, rating FROM ratings")
    ratings = c.fetchall()

    total_users = len(users)

    c.execute("SELECT AVG(rating) FROM ratings")
    avg = c.fetchone()[0] or 0

    percent = round((avg / 5) * 100, 2) if avg else 0

    conn.close()

    return render_template("admin.html",
                           users=users,
                           ratings=ratings,
                           total_users=total_users,
                           avg=round(avg,2),
                           percent=percent)

# -------- RUN --------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
