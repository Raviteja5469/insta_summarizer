# Test script
from src.downloaders.instagram import InstagramDownloader
from src.extractors.audio import extract_audio
from src.processors.audio import AudioProcessor
from src.processors.visual import VideoProcessor
from src.processors.evaluator import Evaluator

downloader = InstagramDownloader()
audio_processor = AudioProcessor()
video_processor = VideoProcessor()
evaluator = Evaluator()

# video_path = downloader.download("https://www.instagram.com/reel/DPeG4jdjEAA")
# print(f"Video path: {video_path}")

# audio_path = extract_audio("")
# print(f"Audio path: {audio_path}")

# audio_result = audio_processor.process("temp_files/reel_DPeG4jdjEAA/DPeG4jdjEAA.wav")
# print(f"Transcript: {audio_result}")

video_path = "temp_files/reel_DPeG4jdjEAA/DPeG4jdjEAA.mp4"
evaluation = evaluator.decide(video_path, 0.9763033)
print(f"Evaluation: {evaluation}")

if evaluation['decision']:
    video_summary = video_processor.process(video_path)
    print(f"Video summary: {video_summary}")    
else:
    print("Skipping visual summarization based on evaluation.")