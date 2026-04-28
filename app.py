from flask import Flask, render_template, request, redirect, session
import sqlite3, time
from werkzeug.security import generate_password_hash, check_password_hash
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = "secretkey"

# ---------- CLOUDINARY CONFIG ----------
cloudinary.config(
    cloud_name="dpbsztgph",
    api_key="455596988582446",
    api_secret="YOUR_NEW_SECRET"
)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY, username TEXT, message TEXT, file_url TEXT, folder TEXT, time TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS folders(id INTEGER PRIMARY KEY, username TEXT, folder_name TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS ratings(id INTEGER PRIMARY KEY, username TEXT, rating INTEGER)")

    conn.commit()
    conn.close()

init_db()

# ---------- ICON ----------
def get_icon(name):
    if name.endswith((".png",".jpg",".jpeg")):
        return "🖼️"
    if name.endswith(".pdf"):
        return "📄"
    if name.endswith((".doc",".docx")):
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
            return "User exists"
        conn.close()
        return redirect("/")
    return render_template("register.html")

# ---------- LOGIN ----------
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

    return "Invalid Login"

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

    c.execute("SELECT file_url, message FROM posts WHERE username=? AND folder=?",
              (session["user"], folder))
    posts = c.fetchall()

    conn.close()

    return render_template("dashboard.html",
                           folders=folders,
                           posts=posts,
                           current_folder=folder)

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

    url = ""
    if file:
        result = cloudinary.uploader.upload(file)
        url = result["secure_url"]

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("INSERT INTO posts VALUES(NULL,?,?,?,?,?)",
              (session["user"], file.filename, url, folder, time.time()))
    conn.commit()
    conn.close()

    return redirect(f"/dashboard?folder={folder}")

# ---------- DELETE ----------
@app.route("/delete", methods=["POST"])
def delete():
    url = request.form["url"]

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("DELETE FROM posts WHERE file_url=?", (url,))
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
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT username FROM users")
    users = c.fetchall()

    c.execute("SELECT username, rating FROM ratings")
    ratings = c.fetchall()

    conn.close()

    return render_template("admin.html",
                           users=users,
                           ratings=ratings)

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
