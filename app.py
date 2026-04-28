from flask import Flask, render_template, request, redirect, session
import sqlite3, os, time
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------- DATABASE --------
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        folder_name TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        filename TEXT,
        folder TEXT,
        size INTEGER,
        timestamp REAL
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
            c.execute("INSERT INTO users (username,password) VALUES (?,?)",
                      (request.form["username"],
                       generate_password_hash(request.form["password"])))
            conn.commit()
        except:
            return "User exists ❌"

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

    return "Invalid ❌"

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

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT folder_name FROM folders WHERE username=?",
              (session["user"],))
    folders = c.fetchall()

    c.execute("SELECT filename,message,folder FROM posts WHERE username=?",
              (session["user"],))
    posts = c.fetchall()

    c.execute("SELECT SUM(size) FROM posts WHERE username=?",
              (session["user"],))
    total = c.fetchone()[0] or 0
    storage = round(total/(1024*1024),2)

    conn.close()

    return render_template("dashboard.html",
                           folders=folders,
                           posts=posts,
                           storage=storage)

# -------- CREATE FOLDER --------
@app.route("/create_folder", methods=["POST"])
def create_folder():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("INSERT INTO folders VALUES (NULL,?,?)",
              (session["user"], request.form["folder"]))

    conn.commit()
    conn.close()
    return redirect("/dashboard")

# -------- OPEN FOLDER --------
@app.route("/folder/<name>")
def folder(name):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT filename,message,folder FROM posts WHERE username=? AND folder=?",
              (session["user"], name))
    posts = c.fetchall()

    c.execute("SELECT folder_name FROM folders WHERE username=?",
              (session["user"],))
    folders = c.fetchall()

    conn.close()

    return render_template("dashboard.html", posts=posts, folders=folders)

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
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("UPDATE folders SET folder_name=? WHERE folder_name=? AND username=?",
              (request.form["new"], request.form["old"], session["user"]))

    c.execute("UPDATE posts SET folder=? WHERE folder=? AND username=?",
              (request.form["new"], request.form["old"], session["user"]))

    conn.commit()
    conn.close()
    return redirect("/dashboard")

# -------- SEARCH --------
@app.route("/search")
def search():
    q = request.args.get("q")

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT filename,message,folder FROM posts WHERE username=? AND message LIKE ?",
              (session["user"], "%"+q+"%"))

    posts = c.fetchall()

    c.execute("SELECT folder_name FROM folders WHERE username=?",
              (session["user"],))
    folders = c.fetchall()

    conn.close()

    return render_template("dashboard.html", posts=posts, folders=folders)

# -------- UPLOAD --------
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    folder = request.form["folder"]
    message = request.form["message"]

    filename = ""
    size = 0

    if file and file.filename:
        filename = str(int(time.time()))+"_"+file.filename
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        size = os.path.getsize(path)

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""INSERT INTO posts VALUES(NULL,?,?,?,?,?,?)""",
              (session["user"], message, filename, folder, size, time.time()))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

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

# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)
