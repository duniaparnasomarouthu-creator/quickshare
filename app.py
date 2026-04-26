from flask import Flask, render_template, request
import os

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    return render_template("result.html")

# ⭐ NEW: Gallery page
@app.route("/gallery")
def gallery():
    images = os.listdir(UPLOAD_FOLDER)
    images = ["uploads/" + img for img in images]
    return render_template("gallery.html", images=images)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
