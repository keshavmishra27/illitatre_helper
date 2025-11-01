#importing libraries
from flask import Flask, render_template, request, jsonify
from PIL import Image
import pytesseract
import io
from flask_cors import CORS

#creating app
app = Flask(__name__)
#need backend routes to connect with frontend
CORS(app)

# Path to tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#function to extract text from image using OCR
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

#home page
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

#route to handle file upload and text extraction
@app.route('/upload', methods=['POST'])
def upload_file():
    
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected."}), 400

    text = extract_text_from_image(file)

    
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
        
        return jsonify({"extracted_text": text})

#run app
if __name__ == '__main__':
    app.run(debug=True)
