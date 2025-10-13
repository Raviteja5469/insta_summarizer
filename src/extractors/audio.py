import moviepy
from src.config import logger

def extract_audio(video_path: str) -> str:
    audio_path = f"{video_path}.wav"
    try:
        clip = moviepy.VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path, codec='pcm_s16le', fps=44100, logger=None)
        clip.close()
        logger.info(f"Extracted audio to {audio_path}")
        return audio_path
    except Exception as e:
        raise RuntimeError(f"Audio extraction failed: {e}")