import os
import whisper
import torch
from src.config import logger
from typing import Optional, Dict
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

class AudioProcessor:
    """
    A class to handle audio processing: speech detection, transcription,
    and translation directly to English. It dynamically selects the Whisper model
    based on the detected language and calculates the speech presence ratio.
    """
    def __init__(self):
        """
        Initializes the processor. Models are loaded dynamically and cached to be efficient.
        """
        self.models = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"AudioProcessor initialized. Models will be loaded on demand on '{self.device}'.")

    def _get_model(self, model_size: str):
        """
        Private method to load a Whisper model into memory if not already cached.
        This avoids reloading models from disk repeatedly.
        """
        if model_size not in self.models:
            logger.info(f"Loading Whisper model '{model_size}'...")
            self.models[model_size] = whisper.load_model(model_size, device=self.device)
            logger.info(f"Whisper model '{model_size}' loaded successfully.")
        return self.models[model_size]
    
    def _estimate_speech_ratio(self, audio_path: str, silence_thresh: float = -35.0, min_silence_len: int = 500) -> float:
        try:
            audio = AudioSegment.from_file(audio_path)
            nonsilent_ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
            speech_duration_ms = sum(end - start for start, end in nonsilent_ranges)
            total_duration_ms = len(audio)
            ratio = speech_duration_ms / total_duration_ms if total_duration_ms > 0 else 0.0
            logger.info(f"Estimated speech ratio (pre-transcription): {ratio:.2f}")
            return ratio
        except Exception as e:
            logger.error(f"Error estimating speech ratio: {e}")
            return 0.0

    def _has_speech(self, audio_path: str, threshold: float = -35.0) -> bool:
        """
        Private method to detect if the audio contains speech.
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            loudness = audio.dBFS
            logger.info(f"Audio loudness: {loudness:.2f} dBFS. Threshold: {threshold} dBFS.")
            return loudness != float('-inf') and loudness > threshold
        except Exception as e:
            logger.error(f"Could not analyze audio for speech detection: {e}")
            return False

    def process(self, audio_path: str) -> Optional[Dict]:
        """
        Runs the full pipeline:
        1. Detects spoken language.
        2. Dynamically selects Whisper model.
        3. Transcribes (and translates to English if needed).
        4. Calculates speech ratio.
        """
        logger.info(f"Starting audio processing for: {audio_path}")
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return None

        if not self._has_speech(audio_path):
            logger.warning("No clear speech detected. Skipping transcription.")
            return {"transcript": None, "speech_ratio": 0.0}
        
        speech_ratio = self._estimate_speech_ratio(audio_path)
        if speech_ratio < 0.2:
            logger.info("Low speech ratio detected, skipping transcription.")
            return {"transcript": None, "speech_ratio": speech_ratio}
        
        try:
            # Step 1: Load small/base model for language detection
            detection_model = self._get_model("base")

            # Load the audio
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio) 
            mel = whisper.log_mel_spectrogram(audio).to(detection_model.device)

            # Step 2: Detect language
            _, lang_probs = detection_model.detect_language(mel)
            detected_language = max(lang_probs, key=lang_probs.get)
            logger.info(f"Detected language: {detected_language}")

            # Step 3: Choose transcription model
            if detected_language == "en":
                model_size = "small"
                task_type = "transcribe"
            else:
                model_size = "medium"
                task_type = "translate"

            transcription_model = self._get_model(model_size)
            logger.info(f"Using '{model_size}' model for {task_type} task.")

            # Step 4: Transcribe
            result = transcription_model.transcribe(
                audio_path,
                task=task_type,
                temperature=0.0,
                beam_size=5,
                verbose=False
            )

            english_transcript = result.get("text", "").strip()

            # Step 5: Calculate speech ratio
            total_duration_s = len(AudioSegment.from_file(audio_path)) / 1000.0
            speech_duration_s = sum(
                seg.get("end", 0) - seg.get("start", 0)
                for seg in result.get("segments", [])
            )
            speech_ratio = (speech_duration_s / total_duration_s) if total_duration_s > 0 else 0
            logger.info(f"Speech ratio calculated: {speech_ratio:.2f}")

            if not english_transcript:
                logger.warning("Transcription resulted in an empty string.")
                return {"transcript": None, "speech_ratio": speech_ratio}

            logger.info("Successfully generated transcript.")
            return {
                "transcript": english_transcript,
                "speech_ratio": speech_ratio,
                "detected_language": detected_language
            }

        except Exception as e:
            logger.error(f"Error during transcription/translation: {e}")
            return None
