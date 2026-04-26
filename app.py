from flask import Flask, request, render_template, send_from_directory
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads folder if not exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    if file:
        filename = str(uuid.uuid4()) + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        link = f"http://127.0.0.1:5000/image/{filename}"
        return render_template('result.html', link=link, filename=filename)
    return "No file selected"

@app.route('/image/<filename>')
def image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
