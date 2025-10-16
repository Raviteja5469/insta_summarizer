import moviepy
from src.config import logger
from typing import Optional

def extract_audio(video_path: str) -> Optional[str]:
    """
    Extracts an audio track from a video file if one exists.

    Returns:
        The path to the audio file, or None if no audio track is found.
    """
    audio_path = f"{video_path.split('.')[0]}.wav"
    clip = None 
    
    try:
        clip = moviepy.VideoFileClip(video_path)
        if clip.audio:
            clip.audio.write_audiofile(
                audio_path, 
                codec='pcm_s16le', 
                fps=44100, 
                logger=None
            )
            logger.info(f"Successfully extracted audio to {audio_path}")
            return audio_path
        else:
            # Handle the case where there is no audio
            logger.warning(f"Video file has no audio track: {video_path}")
            return None
            
    except Exception as e:
        logger.error(f"Audio extraction failed for {video_path}: {e}")
        return None
        
    finally:
        if clip:
            clip.close()