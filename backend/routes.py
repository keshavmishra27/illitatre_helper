from flask import Blueprint, request, jsonify, Response, render_template
import base64 # For audio encoding

# --- Import Core Services and Models ---
# The following imports assume your helper functions are defined in models.py
from .models import UserDetail, get_db_user_details, store_db_user_details 
from .agent import process_agent_query
from .speech_services import transcribe_audio_api, synthesize_speech_api
# Import the new OCR helper functions
from .ocr_helpers import extract_text_from_image, parse_extracted_text


# --- Define the Blueprint ---
main_blueprint = Blueprint('main_blueprint', __name__)


# --- 1. VOICE AGENT ROUTES ---

@main_blueprint.route('/', methods=['GET'])
def index():
    """Renders the main Voice Agent application page (index.html)."""
    user_details = get_db_user_details() or {'name': 'N/A', 'age': 0, 'language': 'en'}
    return render_template('index.html', user=user_details)


@main_blueprint.route('/chat_audio', methods=['POST'])
def chat_audio():
    """
    Handles the full Speech-to-Speech loop: STT -> LLM -> TTS, returning JSON.
    """
    if 'audio_file' not in request.files:
        return jsonify({"error": "No audio file uploaded. Please send audio/mp3/wav data."}), 400
    
    audio_file = request.files['audio_file']
    audio_content = audio_file.read()

    current_details = get_db_user_details() 
    lang_code = current_details.get('language', 'en') 

    # Step 1: STT - Convert audio to text
    user_query = transcribe_audio_api(audio_content, lang_code)
    
    if not user_query:
        error_msg = {"en": "I did not catch that. Could you please repeat?", "es": "No te he entendido. ¿Podrías repetir?"}.get(lang_code, "I did not catch that.")
        audio_bytes = synthesize_speech_api(error_msg, lang_code)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return jsonify({
            'error': 'Transcription failed.', 
            'ai_response_text': error_msg, 
            'audio_base64': audio_base64,
            'user_details_updated': current_details
        }), 400

    # Step 2: LLM Processing - Processes text, manages state, and stores data
    # Note: If an error occurs inside process_agent_query, it is re-raised and handled 
    # by the application's general error handling (which we assume is robust).
    ai_response_text, is_complete = process_agent_query(user_query)

    # Step 3: TTS - Convert text response to audio
    latest_details = get_db_user_details()
    current_lang = latest_details.get('language', 'en')
    
    audio_response_bytes = synthesize_speech_api(ai_response_text, current_lang)
    
    # Step 4: Base64 Encode Audio and RETURN JSON
    audio_base64 = base64.b64encode(audio_response_bytes).decode('utf-8')

    return jsonify({
        'ai_response_text': ai_response_text,
        'audio_base64': audio_base64,
        'user_details_updated': latest_details,
        'is_setup_complete': is_complete
    })

@main_blueprint.route('/user_details', methods=['GET'])
def user_details_api():
    """API endpoint to get the latest user details."""
    details = get_db_user_details() or {'name': 'N/A', 'age': 0, 'language': 'en'}
    return jsonify(details)


# --- 2. OCR FEATURE ROUTES ---

@main_blueprint.route('/ocr', methods=['GET'])
def ocr_page():
    """Renders the dedicated OCR page (templates/ocr.html)."""
    return render_template('ocr.html')


@main_blueprint.route('/ocr_upload', methods=['POST'])
def ocr_upload():
    """
    Receives an image file, extracts text, and returns parsed data via JSON.
    This replaces the old '/upload' endpoint.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected."}), 400

    # 1. Extract raw text (using helper from ocr_helpers.py)
    text = extract_text_from_image(file)

    if text.startswith("ERROR:"):
        return jsonify({"error": text}), 500 # Return 500 if OCR tool failed
        
    # 2. Parse key-value data (using helper from ocr_helpers.py)
    parsed = parse_extracted_text(text)

    if parsed:
        # Return structured data and raw text
        return jsonify({"parsed_data": parsed, "raw_text": text})
    else:
        # Return raw text if no structured data was found
        return jsonify({"extracted_text": text})

# Note: The duplicate index and manual function definition have been removed.
