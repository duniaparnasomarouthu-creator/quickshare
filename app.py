from flask import Flask, render_template, request
import os
import random

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# store code → filename
data_store = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]

    # generate secret code
    code = str(random.randint(1000, 9999))

    filename = code + "_" + file.filename
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # save mapping
    data_store[code] = filename

    return render_template("result.html", code=code)

@app.route("/view", methods=["GET", "POST"])
def view():
    image_url = None
    error = None

    if request.method == "POST":
        code = request.form["code"]

        if code in data_store:
            image_url = "uploads/" + data_store[code]
        else:
            error = "Invalid Code ❌"

    return render_template("view.html", image_url=image_url, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
