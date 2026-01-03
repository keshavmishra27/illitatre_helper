from flask import Blueprint, request, jsonify, render_template
from .models import get_db_user_details
from .speech_services import handle_uploaded_audio
from .ocr_helpers import extract_text_from_image, parse_extracted_text

main_blueprint = Blueprint('main_blueprint', __name__)

# -------------------- 1. VOICE AGENT --------------------
@main_blueprint.route('/', methods=['GET'])
def index():
    """Render the Voice Agent main page."""
    user_details = get_db_user_details() or {'name': 'N/A', 'age': 0, 'language': 'en'}
    return render_template('index.html', user=user_details)


@main_blueprint.route("/chat_audio", methods=["GET", "POST"])
def chat_audio():
    """Handle audio input and return transcription."""
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    audio_file = request.files['audio_file']
    audio_bytes = audio_file.read()

    text = handle_uploaded_audio(audio_bytes, lang_code="en-IN")

    if not text:
        return jsonify({"error": "Transcription failed"}), 400

    return jsonify({"transcribed_text": text})


# -------------------- 2. USER DETAILS --------------------
@main_blueprint.route('/user_details', methods=['GET'])
def user_details_api():
    details = get_db_user_details() or {'name': 'N/A', 'age': 0, 'language': 'en'}
    return jsonify(details)


# -------------------- 3. OCR FEATURE --------------------
@main_blueprint.route('/ocr', methods=['GET'])
def ocr_page():
    return render_template('ocr.html')


@main_blueprint.route('/ocr_upload', methods=['POST'])
def ocr_upload():
    """Handles OCR image upload and parsing."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected."}), 400

    text = extract_text_from_image(file)
    if text.startswith("ERROR:"):
        return jsonify({"error": text}), 500

    parsed = parse_extracted_text(text)
    if parsed:
        return jsonify({"parsed_data": parsed, "raw_text": text})
    else:
        return jsonify({"extracted_text": text})
