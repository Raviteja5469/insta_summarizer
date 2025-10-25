import cv2
import numpy as np
import google.generativeai as genai
from typing import List
from src.config import Config, logger
import os

genai.configure(api_key=Config.GOOGLE_API_KEY)

class VideoProcessor:
    """
    Processes video by extracting keyframes and generating a visual summary
    using the cost-effective Gemini 1.5 Flash model.
    """

    def __init__(self):
        """Initializes the Gemini model client."""
        try:
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel("gemini-2.0-flash-lite")
            logger.info("Initialized video processor with gemini-2.0-flash-lite.")
        except Exception as e:
            logger.error(f"Failed to configure Google Gemini client: {e}")
            self.model = None

    def _extract_smart_keyframes(self, video_path: str, threshold: float = 5.0, max_frames: int = 10) -> List[np.ndarray]:
        frames = []
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video file: {video_path}")
            return []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        interval = max(total_frames // (max_frames * 2), 1)  # balance scene + distribution

        prev_gray = None
        frame_id = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_id % interval == 0:
                frame_resized = cv2.resize(frame, (512, 512))
                gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)

                if prev_gray is None or np.mean(cv2.absdiff(prev_gray, gray)) > threshold:
                    frames.append(frame_resized)
                    prev_gray = gray

                if len(frames) >= max_frames:
                    break
            frame_id += 1

        cap.release()
        logger.info(f"Extracted {len(frames)} distributed keyframes across video.")
        return frames


    def _generate_visual_summary(self, frames: List[np.ndarray]) -> str:
        """
        Sends a sequence of keyframes to the Gemini model in a single API call
        to generate a coherent visual summary.
        """
        if not frames:
            return "No significant visual information was extracted from the video."

        # 1. Define the text part of the prompt
        prompt_text = """
                    You are a technical analyst. The following is a sequence of keyframes from an informational video.
                    Your task is to create a single, concise summary of the visual content.
                    - Analyze the frames in order to understand the flow of information.
                    - Transcribe any important text, code snippets, or commands you see clearly.
                    - Describe any key diagrams, charts, or user interface elements.
                    - Synthesize all of this into one coherent summary of what is being shown.
                    """

        # 2. Prepare the prompt parts for the API call (text + images)
        prompt_parts = [prompt_text]
        for frame in frames:
            # Encode frame to JPEG bytes and prepare it for the API
            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                logger.warning("Failed to encode a frame.")
                continue

            # The Gemini Python SDK works well with these blob objects
            prompt_parts.append({"mime_type": "image/jpeg", "data": buffer.tobytes()})

        # 3. Make the single API call to Gemini
        try:
            logger.info(
                f"Making a single API call to Gemini with {len(frames)} frames..."
            )
            response = self.model.generate_content(prompt_parts)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Visual summary generation failed with Gemini API: {e}")
            return "Failed to generate visual summary due to an API error."

    def process(self, video_path: str, max_frames: int = 10) -> str:
        """
        Runs the full, cost-optimized video processing pipeline.

        Args:
            video_path (str): The path to the video file.
            max_frames (int): The maximum number of keyframes to extract and send.
                              This is the primary lever for controlling API cost.

        Returns:
            str: The generated visual summary.
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found at: {video_path}")
            return "Error: Video file not found."

        frames = self._extract_smart_keyframes(
            video_path, threshold=5.0, max_frames=max_frames
        )
        summary = self._generate_visual_summary(frames)
        return summary
