import cv2
import pytesseract
import numpy as np
from src.config import logger

class Evaluator:
    """
    Evaluates video and audio metrics to decide if running the expensive
    visual summarizer is justified.
    """
    def __init__(
        self,
        # Visual thresholds
        text_ratio_threshold: float = 0.2,
        scene_diversity_threshold: float = 0.4,
        # Audio threshold
        speech_reliance_threshold: float = 0.75, # If speech is >75%, we can likely rely on it
        # Internal settings
        min_text_length: int = 15,
        samples: int = 10
    ):
        self.text_ratio_threshold = text_ratio_threshold
        self.scene_diversity_threshold = scene_diversity_threshold
        self.speech_reliance_threshold = speech_reliance_threshold
        self.min_text_length = min_text_length
        self.samples = samples
        logger.info("Evaluator initialized with combined audio/visual thresholds.")

    def _evaluate_visuals(self, video_path: str) -> dict:
        """
        Private method to calculate only the visual metrics.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"text_ratio": 0, "scene_diversity": 0}

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, frame_count // self.samples)
        num_samples_to_take = self.samples if frame_count >= self.samples else frame_count

        text_frame_count = 0
        scene_diversity_scores = []
        prev_hist = None
        
        try:
            for i in range(num_samples_to_take):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i * step)
                ret, frame = cap.read()
                if not ret: 
                    continue

                hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
                if prev_hist is not None:
                    score = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)
                    scene_diversity_scores.append(score)
                prev_hist = hist

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                text = pytesseract.image_to_string(thresh, config='--psm 6')
                if len(text.strip()) > self.min_text_length:
                    text_frame_count += 1
        finally:
            cap.release()

        avg_scene_diversity = np.mean(scene_diversity_scores) if scene_diversity_scores else 0
        text_presence_ratio = text_frame_count / num_samples_to_take
        
        return {
            "text_ratio": text_presence_ratio,
            "scene_diversity": avg_scene_diversity,
        }

    def decide(self, video_path: str, speech_ratio: float) -> dict:
        """
        Makes a final decision based on both visual and audio metrics.
        
        Returns a dictionary with all metrics and the final decision.
        """
        visual_metrics = self._evaluate_visuals(video_path)
        text_ratio = visual_metrics["text_ratio"]
        scene_diversity = visual_metrics["scene_diversity"]
        
        logger.info(
            f"Final Evaluation Metrics - Speech Ratio: {speech_ratio:.2f}, "
            f"Text Presence: {text_ratio:.2f}, Scene Diversity: {scene_diversity:.2f}"
        )

        # --- Decision Logic ---
        # Rule 1: If visuals are clearly informative, always process them.
        if text_ratio >= self.text_ratio_threshold:
            reason = "High text presence detected. Visuals are critical."
            run_visual_summarizer = True
        elif scene_diversity >= self.scene_diversity_threshold:
            reason = "High scene diversity detected. Visuals are dynamic and important."
            run_visual_summarizer = True
        
        # Rule 2: If visuals are NOT clearly informative, check the audio.
        elif speech_ratio >= self.speech_reliance_threshold:
            reason = "Visuals are static, but speech ratio is high. Relying on audio transcript."
            run_visual_summarizer = False
        
        # Rule 3: If visuals are low AND speech is low, there's not much information to get.
        else:
            reason = "Low visual activity and low speech content. Likely not an informational video."
            run_visual_summarizer = False
            
        return {
            "decision": run_visual_summarizer,
            "reason": reason,
            **visual_metrics,
            "speech_ratio": speech_ratio,
        }