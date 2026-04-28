from flask import Flask, render_template, request, redirect, session
import sqlite3, os, time
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------- DB INIT (SAFE FOR OLD DATA) --------
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )""")

    # Add columns safely
    try:
        c.execute("ALTER TABLE posts ADD COLUMN folder TEXT DEFAULT 'root'")
    except:
        pass

    try:
        c.execute("ALTER TABLE posts ADD COLUMN size INTEGER DEFAULT 0")
    except:
        pass

    c.execute("""CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        folder_name TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        rating INTEGER
    )""")

    conn.commit()
    conn.close()

init_db()

# -------- HOME --------
@app.route("/")
def home():
    return render_template("login.html")

# -------- REGISTER --------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        conn = sqlite3.connect("data.db")
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users VALUES(NULL,?,?)",
                      (request.form["username"],
                       generate_password_hash(request.form["password"])))
            conn.commit()
        except:
            return "User already exists ❌"

        conn.close()
        return redirect("/")
    return render_template("register.html")

# -------- LOGIN --------
@app.route("/login", methods=["POST"])
def login():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE username=?",
              (request.form["username"],))
    user = c.fetchone()
    conn.close()

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

    c.execute("SELECT folder_name FROM folders WHERE username=?",
              (session["user"],))
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

    percent = round((avg/5)*100,2) if avg else 0

    conn.close()

    return render_template("admin.html",
                           users=users,
                           ratings=ratings,
                           total_users=total_users,
                           avg=round(avg,2),
                           percent=percent)

# -------- ERROR FIX --------
@app.errorhandler(404)
def not_found(e):
    return redirect("/")

# -------- RUN (IMPORTANT FOR RENDER) --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
