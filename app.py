from flask import Flask, render_template, request
import os
import sqlite3
import random
import time

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS images (
            code TEXT PRIMARY KEY,
            filename TEXT,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- UPLOAD ----------------
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]

    if file.filename == "":
        return "No file selected"

    code = str(random.randint(1000, 9999))

    filename = code + "_" + file.filename
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # save to DB with time
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO images VALUES (?, ?, ?)",
        (code, filename, time.time())
    )
    conn.commit()
    conn.close()

    return render_template("result.html", code=code)

# ---------------- VIEW ----------------
@app.route("/view", methods=["GET", "POST"])
def view():
    image_url = None
    error = None

    if request.method == "POST":
        code = request.form["code"]

        conn = sqlite3.connect("data.db")
        c = conn.cursor()
        c.execute("SELECT filename, timestamp FROM images WHERE code=?", (code,))
        result = c.fetchone()
        conn.close()

        if result:
            filename, timestamp = result

            # expiry check (1 hour = 3600 sec)
            if time.time() - timestamp > 3600:
                error = "Code Expired ⏰"

                # delete expired record
                conn = sqlite3.connect("data.db")
                c = conn.cursor()
                c.execute("DELETE FROM images WHERE code=?", (code,))
                conn.commit()
                conn.close()

            else:
                image_url = "uploads/" + filename
        else:
            error = "Invalid Code ❌"

    return render_template("view.html", image_url=image_url, error=error)

# ---------------- DELETE ----------------
@app.route("/delete", methods=["POST"])
def delete():
    code = request.form["code"]

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT filename FROM images WHERE code=?", (code,))
    result = c.fetchone()

    if result:
        filename = result[0]

        # delete file
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # delete from DB
        c.execute("DELETE FROM images WHERE code=?", (code,))
        conn.commit()

        msg = "Deleted Successfully 🗑️"
    else:
        msg = "Code not found ❌"

    conn.close()

    return msg

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
