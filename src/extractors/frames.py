import cv2
from PIL import Image
import os
from src.config import Config, logger

def extract_and_compress_frames(video_path: str, interval: int = 60, max_frames: int = 3, compress_size: tuple = (320, 240)) -> list:
    vidcap = cv2.VideoCapture(video_path)
    count, compressed_frames = 0, []
    try:
        while len(compressed_frames) < max_frames:
            success, image = vidcap.read()
            if not success:
                break
            if count % interval == 0:
                frame_path = f"{Config.TEMP_DIR}/frame_{count}.jpg"
                cv2.imwrite(frame_path, image)
                # Compress
                img = Image.open(frame_path)
                img.thumbnail(compress_size)
                compressed_path = f"{Config.TEMP_DIR}/compressed_frame_{count}.jpg"
                img.save(compressed_path, "JPEG")
                compressed_frames.append(compressed_path)
                os.remove(frame_path)  # Cleanup original frame
            count += 1
        logger.info(f"Extracted and compressed {len(compressed_frames)} frames")
        return compressed_frames
    finally:
        vidcap.release()