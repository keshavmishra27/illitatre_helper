from flask import Flask, render_template, request, jsonify
from PIL import Image
import pytesseract
import io
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Set Tesseract executable path if needed (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# If Tesseract is on PATH, you can comment the above line.

def extract_text_from_image(uploaded_file):
    """
    Return OCR text (string). uploaded_file is a FileStorage.
    """
    try:
        uploaded_file.seek(0)
        img_bytes = uploaded_file.read()
        img = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(img)
        return text or ""
    except Exception as e:
        return f"ERROR: {e}"

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Expecting 'file' in request.files
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected."}), 400

    text = extract_text_from_image(file)

    # Try to parse key=value lines into a dict, otherwise return full text
    parsed = {}
    for line in text.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            k = key.strip()
            v = value.strip()
            if k:
                parsed[k] = v

    if parsed:
        return jsonify(parsed)
    else:
        # return as single string under key 'extracted_text'
        return jsonify({"extracted_text": text})

if __name__ == '__main__':
    app.run(debug=True)
