from src.config import logger
from src.config import Config
from src.downloaders.instagram import InstagramDownloader
from src.extractors.audio import extract_audio
from src.extractors.frames import extract_and_compress_frames
from src.processors.transcribe import transcribe_audio
from src.summarizers.multimodal import generate_multimodal_summary
from src.summarizers.rag import gemini_summarize_with_rag
import os
import shutil

def run_pipeline(url: str, target_lang: str = "English") -> dict:
    downloader = InstagramDownloader()
    video_path = None
    audio_path = None
    compressed_frames = []

    try:
        video_path = downloader.download(url)
        audio_path = extract_audio(video_path)
        transcript = transcribe_audio(audio_path)

        compressed_frames = extract_and_compress_frames(video_path)
        frame_descriptions = generate_multimodal_summary(transcript, audio_path, compressed_frames)
        final_summary = gemini_summarize_with_rag(transcript, frame_descriptions, target_lang)

        output = {
            "transcript": transcript,
            "frame_descriptions": frame_descriptions,
            "summary": final_summary
        }
        logger.info("Pipeline complete")
        return output
    
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

    finally:
        # Cleanup
        cleanup_paths = [audio_path] + compressed_frames
        if video_path:  # Keep video for debugging if pipeline fails later
            cleanup_paths.append(video_path)
        
        for path in cleanup_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    logger.debug(f"Cleaned: {path}")
                except Exception as e:
                    logger.warning(f"Cleanup failed for {path}: {e}")