import os
import tempfile
import subprocess
import warnings
try:
    import torch
except ImportError:
    torch = None

from pathlib import Path

# whisper import (vanilla whisper)
try:
    import whisper
except ImportError:
    whisper = None

# FFmpeg path (same as before)
FFMPEG_PATH = r"E:\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
os.environ["PATH"] += os.pathsep + os.path.dirname(FFMPEG_PATH)

# Limit threads to avoid total CPU lock
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
torch.set_num_threads(2)

print(" FFmpeg path set to:", FFMPEG_PATH)
print("OMP/OPENBLAS/Torch threads limited to 2")

# Lazy-load model global (load on first request)
_whisper_model = None
def get_whisper_model(name="large"):
    global _whisper_model
    if _whisper_model is None:
        print(f"[Whisper] Loading model: {name} (this may take a moment)")
        # force CPU device
        _whisper_model = whisper.load_model(name, device="cpu")
        print("[Whisper] model loaded")
    return _whisper_model

def convert_to_wav(webm_bytes):
    """Convert uploaded WebM/Opus → WAV (mono, 16kHz) using explicit format/codec."""
    try:
        cmd = [
            FFMPEG_PATH,
            "-f", "webm",
            "-codec:a", "opus",
            "-i", "pipe:0",
            "-ac", "1",
            "-ar", "16000",
            "-f", "wav",
            "pipe:1"
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(input=webm_bytes, timeout=30)
        if proc.returncode != 0:
            print("[ffmpeg ERROR]:", err.decode(errors="ignore"))
            return None
        print("[ffmpeg SUCCESS] WAV generated")
        return out
    except subprocess.TimeoutExpired:
        proc.kill()
        print("[ffmpeg ERROR]: timeout")
        return None
    except Exception as e:
        print("[ffmpeg EXCEPTION]:", e)
        return None

def transcribe_audio_api(wav_bytes, lang_code=None, model_name="large"):
    """Transcribe WAV bytes using Whisper (returns dict with text and detected lang)."""
    temp_wav_path = None
    try:
        model = get_whisper_model(model_name)

        # write temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            tf.write(wav_bytes)
            temp_wav_path = tf.name

        print(f"[Whisper] Transcribing audio... (lang hint: {lang_code})")
        # Use language hint only if provided and valid; otherwise let Whisper auto-detect
        transcribe_kwargs = {}
        if lang_code:
            transcribe_kwargs["language"] = lang_code.split("-")[0].lower()

        result = model.transcribe(temp_wav_path, **transcribe_kwargs)
        text = result.get("text", "").strip()
        detected_lang = result.get("language", None)  # whisper returns detected language code
        print(f"[Whisper] Detected language: {detected_lang} | Text length: {len(text)}")
        print(f"[User said]: {text}")
        return {"text": text, "language": detected_lang}
    except Exception as e:
        print("[Transcription ERROR]:", e)
        return None
    finally:
        try:
            if temp_wav_path and Path(temp_wav_path).exists():
                Path(temp_wav_path).unlink()
        except Exception:
            pass

# Full pipeline
def handle_uploaded_audio(file_bytes, lang_code=None):
    print("[Audio received]:", len(file_bytes), "bytes")
    wav_data = convert_to_wav(file_bytes)
    if not wav_data:
        print("[Conversion ERROR]: Could not convert WebM to WAV")
        return None
    result = transcribe_audio_api(wav_data, lang_code=lang_code, model_name="large")
    if not result:
        print("[Transcription ERROR]: No text returned")
        return None
    return result


