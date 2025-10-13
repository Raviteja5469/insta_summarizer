# Test script
from src.downloaders.instagram import InstagramDownloader
downloader = InstagramDownloader()
video_path = downloader.download("https://www.instagram.com/reel/DNgAaLOzUwa/")
print(f"Video path: {video_path}")