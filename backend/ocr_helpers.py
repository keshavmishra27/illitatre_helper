import io
from PIL import Image
import pytesseract
import re # Needed for simple parsing

# --- OCR Configuration ---
# NOTE: This line is required ONLY if Tesseract is not installed in your system's PATH.
# If you are on Windows and installed Tesseract, uncomment and set the correct path:
#pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_image(uploaded_file):
    """
    Returns OCR text (string) from an uploaded image file (FileStorage object).
    """
    try:
        # Seek to the beginning of the file stream and read bytes
        uploaded_file.seek(0)
        img_bytes = uploaded_file.read()
        
        # Open image using PIL from the byte stream
        img = Image.open(io.BytesIO(img_bytes))
        
        # Perform OCR
        text = pytesseract.image_to_string(img)
        
        return text.strip() or ""
    except Exception as e:
        # Catch errors related to Tesseract path, file format, etc.
        return f"ERROR: OCR extraction failed. Details: {e}"


def parse_extracted_text(raw_text: str) -> dict:
    """
    Parses key=value pairs from raw OCR text.
    Used by /ocr_upload route.
    """
    parsed = {}
    for line in raw_text.splitlines():
        # Look for a line containing a single '=' sign
        if '=' in line:
            # Simple split by the first '=' sign only
            key, value = line.split('=', 1)
            k = key.strip()
            v = value.strip()
            # Only add if the key is not empty
            if k:
                parsed[k] = v
                
    return parsed
