import whisper
from src.config import logger
import os

def transcribe_audio(audio_path: str, model_size: str = "base") -> str:
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    try:
        model = whisper.load_model(model_size)
        result = model.transcribe(audio_path, language="en")  # Assume English; auto-detect if needed
        text = result.get("text", "").strip()
        if not text:
            logger.warning("Empty transcription")
        logger.info("Transcription complete")
        return text
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")