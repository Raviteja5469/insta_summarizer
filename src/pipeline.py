import os
import shutil
from pathlib import Path
from typing import Dict, Any

from src.fetchers.instagram import InstagramDownloader
from src.extractors.audio import extract_audio
from src.processors.audio import AudioProcessor
from src.processors.video import VideoProcessor
from src.processors.evaluator import Evaluator
from src.processors.image import ImageProcessor
from src.config import logger
from src.summarizers.final_summarizer import FinalSummarizer

# --- Module Instantiation ---
downloader = InstagramDownloader()
audio_processor = AudioProcessor()
video_processor = VideoProcessor()
evaluator = Evaluator()
image_processor = ImageProcessor()
summarizer = FinalSummarizer()


def run_pipeline(url: str) -> Dict[str, Any]:
    """
    Runs the full processing pipeline for a given Instagram URL.

    This function handles downloading, content analysis (image/video),
    transcription, evaluation, and summarization, then cleans up all artifacts.

    Args:
        url: The Instagram post or reel URL.

    Returns:
        A dictionary containing all the generated content for final summarization.
    """
    download_result = None
    temp_audio_paths = []
    
    try:
        # STEP 1: Download content from Instagram
        logger.info(f"🚀 Starting pipeline for URL: {url}")
        download_result = downloader.download(url)
        if not download_result:
            raise RuntimeError("Download failed, cannot proceed.")
        
        if download_result.get("folder_path") == "skip":
            logger.info("⏩ Content already downloaded previously. Skipping all processing steps.")
            return {
                "status": "skipped",
                "reason": "Content already downloaded and processed previously.",
                "content_type": download_result.get("content_type"),
            }

        folder_path = Path(download_result["folder_path"])
        content_type = download_result["content_type"]
        logger.info(f"✅ Content downloaded to '{folder_path}' (Type: {content_type})")

        # STEP 2: Initialize the data object for the final summarizer
        summary_data = {
            "description": None,
            "image_summary": None,
            "audio_transcripts": [],
            "video_summaries": [],
        }

        # STEP 3: Extract caption/description from the text file
        # The main text file usually has the same name as the shortcode.
        shortcode = folder_path.name.split('_')[-1]
        description_file = folder_path / f"{shortcode}.txt"
        if description_file.exists():
            summary_data["description"] = description_file.read_text(encoding="utf-8")
            logger.info("📝 Description extracted successfully.")

        # STEP 4: Process images if the content is a post
        # This will run for image-only posts and mixed-media posts.
        if content_type == "post":
            logger.info("🖼️ This is a post. Analyzing images...")
            image_summary_text = image_processor.process(str(folder_path))
            summary_data["image_summary"] = image_summary_text
            logger.info("✅ Image analysis complete.")

        # STEP 5: Process all videos found in the folder (works for Reels and Posts)
        video_files = list(folder_path.glob('*.mp4'))
        if not video_files:
            logger.info("No videos found in this post. Skipping video processing.")
        else:
            logger.info(f"🎥 Found {len(video_files)} video(s). Starting processing loop.")

        for i, video_path in enumerate(video_files):
            logger.info(f"--- Processing Video {i+1}/{len(video_files)}: {video_path.name} ---")
            
            # 5a. Extract Audio
            audio_path = extract_audio(str(video_path))
            temp_audio_paths.append(audio_path) # Mark for cleanup

            if audio_path:
                logger.info(f"🎤 Audio extracted to: {audio_path}")
                audio_result = audio_processor.process(audio_path)
                
                # Check if transcription was successful before proceeding
                if audio_result and audio_result.get("transcript"):
                    summary_data["audio_transcripts"].append(audio_result["transcript"])
                    speech_ratio = audio_result.get("speech_ratio", 0.0)
                    logger.info(f"🗣️ Transcription complete. Speech Ratio: {speech_ratio:.2f}")
                else:
                    logger.warning("Audio processing failed or yielded no transcript.")
                    speech_ratio = 0.0 # Default value for the evaluator
            else:
                # This block runs for SILENT videos
                logger.warning("No audio track found in video. Skipping audio processing.")
                speech_ratio = 0.0 # No audio means 0% speech
                
            # 5c. Evaluate if visual summary is needed
            evaluation = evaluator.decide(str(video_path), speech_ratio)
            logger.info(f"⚖️ Evaluator decision: {evaluation['decision']}. Reason: {evaluation['reason']}")

            # 5d. Generate visual summary if evaluator approves
            if evaluation['decision']:
                video_summary = video_processor.process(str(video_path))
                summary_data["video_summaries"].append(video_summary)
                logger.info("✨ Visual summary generated for the video.")
            else:
                logger.info("Skipping visual summarization based on evaluation.")
        
        logger.info("✅ Pipeline processing complete.")
        
        final_report = summarizer.process(summary_data)
        if final_report:
            return final_report
        else:
            logger.error("Final summarization failed. No report generated.")

    except Exception as e:
        logger.error(f"❌ Pipeline failed for URL {url}: {e}", exc_info=True)
        # Re-raise the exception to be handled by the calling script if needed
        raise

    finally:
        # STEP 6: Cleanup
        logger.info("--- 🧹 Starting Cleanup ---")
        
        # Clean up temporary audio files
        for path in temp_audio_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    logger.debug(f"Cleaned temp file: {path}")
                except Exception as e:
                    logger.warning(f"Cleanup failed for temp file {path}: {e}")

        # Clean up the entire download directory
        if download_result and download_result.get("folder_path"):
            folder_to_delete = download_result["folder_path"]
            if os.path.exists(folder_to_delete):
                try:
                    shutil.rmtree(folder_to_delete)
                    logger.info(f"✅ Successfully cleaned up download directory: {folder_to_delete}")
                except Exception as e:
                    logger.warning(f"Cleanup failed for directory {folder_to_delete}: {e}")
        
        logger.info("--- Cleanup Finished ---")
