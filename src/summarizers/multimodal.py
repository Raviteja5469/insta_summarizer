import google.generativeai as genai
from src.config import Config, logger
import os

genai.configure(api_key=Config.GOOGLE_API_KEY)

def generate_multimodal_summary(transcript: str, audio_path: str = None, image_paths: list = None) -> str:
    model = genai.GenerativeModel("gemini-2.0-flash-lite")  # Valid model
    prompt_parts = [
        f"Transcript: {transcript}",
        "Summarize this Instagram reel content (transcript + visuals/audio). Keep concise, focus on key ideas."
    ]

    if image_paths:
        for path in image_paths:
            prompt_parts.append(genai.upload_file(path=path))

    if audio_path and os.path.exists(audio_path):
        prompt_parts.append(genai.upload_file(path=audio_path))

    try:
        response = model.generate_content(prompt_parts)
        summary = response.text.strip()
        logger.info("Generated multimodal summary")
        return summary
    except Exception as e:
        logger.error(f"Multimodal summary failed: {e}")
        return f"Error: {e}"