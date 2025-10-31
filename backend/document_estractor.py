from flask import Flask, render_template, request, redirect, url_for
from PIL import Image
import pytesseract
import io
import cv2
import numpy as np

app = Flask(__name__)

# ✅ Set path for Tesseract (change if installed elsewhere)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---------- Image Preprocessing (optional but improves accuracy) ----------
def preprocess_image(pil_image):
    # Convert to grayscale
    img = np.array(pil_image.convert("L"))
    # Apply threshold to remove noise
    _, thresh = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
    return Image.fromarray(thresh)

# ---------- OCR Extraction ----------
def extract_text_from_image(uploaded_file):
    try:
        # Reset file pointer (important for Flask)
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)

        # Optional preprocessing (uncomment to use)
        img = preprocess_image(img)

        text = pytesseract.image_to_string(img)

        if not text.strip():
            return "⚠️ OCR completed, but no readable text was detected. Try a clearer image."

        print("Extracted Text:\n", text)  # for debugging in console
        return text

    except Exception as e:
        return f"❌ Error during OCR: {e}"

# ---------- Flask Routes ----------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('home'))

    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('home'))

    if file:
        extracted_text = extract_text_from_image(file)
        return render_template('index.html', extracted_text=extracted_text)

    return redirect(url_for('home'))

# ---------- Run Flask ----------
if __name__ == '__main__':
    app.run(debug=True)
