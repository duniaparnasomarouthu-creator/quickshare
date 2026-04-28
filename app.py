from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3, os, time
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secretkey"

# ---------- STORAGE ----------
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        filename TEXT,
        folder TEXT,
        time TEXT
    )""")

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

# ---------- HELPERS ----------
def get_icon(filename):
    if filename.endswith((".png",".jpg",".jpeg")):
        return "🖼️"
    if filename.endswith(".pdf"):
        return "📄"
    if filename.endswith((".doc",".docx")):
        return "📃"
    return "📁"

app.jinja_env.globals.update(get_icon=get_icon)

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("login.html")

# ---------- REGISTER ----------
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
            return "User exists ❌"

        conn.close()
        return redirect("/")

    return render_template("register.html")

# ---------- LOGIN (FIXED FOR OLD USERS) ----------
@app.route("/login", methods=["POST"])
def login():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE username=?",
              (request.form["username"],))
    user = c.fetchone()
    conn.close()

    if user:
        try:
            if check_password_hash(user[0], request.form["password"]):
                session["user"] = request.form["username"]
                return redirect("/dashboard")
        except:
            pass

        if user[0] == request.form["password"]:
            session["user"] = request.form["username"]
            return redirect("/dashboard")

    return "Invalid login ❌"

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    folder = request.args.get("folder", "root")

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT folder_name FROM folders WHERE username=?", (session["user"],))
    folders = c.fetchall()

    c.execute("""SELECT filename, message FROM posts
                 WHERE username=? AND folder=?""",
              (session["user"], folder))
    posts = c.fetchall()

    conn.close()

    # STORAGE CALC
    total = 50 * 1024 * 1024
    used = 0
    for f in os.listdir(UPLOAD_FOLDER):
        used += os.path.getsize(os.path.join(UPLOAD_FOLDER, f))

    storage = int((used / total) * 100)

    return render_template("dashboard.html",
                           folders=folders,
                           posts=posts,
                           current_folder=folder,
                           storage=storage)

# ---------- CREATE FOLDER ----------
@app.route("/create_folder", methods=["POST"])
def create_folder():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("INSERT INTO folders VALUES(NULL,?,?)",
              (session["user"], request.form["folder"]))

    conn.commit()
    conn.close()
    return redirect("/dashboard")

# ---------- UPLOAD ----------
@app.route("/upload", methods=["POST"])
def upload():
    if "user" not in session:
        return redirect("/")

    file = request.files["file"]
    folder = request.form["folder"]

    filename = ""
    if file and file.filename:
        filename = str(int(time.time())) + "_" + file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("INSERT INTO posts VALUES(NULL,?,?,?,?,?)",
              (session["user"], file.filename, filename, folder, time.time()))

    conn.commit()
    conn.close()

    return redirect(f"/dashboard?folder={folder}")

# ---------- FILE SERVE ----------
@app.route("/files/<filename>")
def files(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ---------- DELETE ----------
@app.route("/delete/<filename>", methods=["POST"])
def delete(filename):
    try:
        os.remove(os.path.join(UPLOAD_FOLDER, filename))
    except:
        pass

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("DELETE FROM posts WHERE filename=?", (filename,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------- RENAME ----------
@app.route("/rename", methods=["POST"])
def rename():
    old = request.form["old"]
    new = request.form["new"]

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("UPDATE posts SET message=? WHERE message=?", (new, old))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------- ADMIN ----------
@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT username FROM users")
    users = c.fetchall()

    c.execute("SELECT username, rating FROM ratings")
    ratings = c.fetchall()

    c.execute("SELECT AVG(rating) FROM ratings")
    avg = c.fetchone()[0] or 0

    conn.close()

    return render_template("admin.html",
                           users=users,
                           ratings=ratings,
                           avg=round(avg,2))

# ---------- RATE ----------
@app.route("/rate", methods=["POST"])
def rate():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("INSERT INTO ratings VALUES(NULL,?,?)",
              (session["user"], request.form["rating"]))

    conn.commit()
    conn.close()
    return redirect("/dashboard")

# ---------- ERROR ----------
@app.errorhandler(404)
def not_found(e):
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
