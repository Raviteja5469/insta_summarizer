import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Central config
class Config:
    INSTA_USERNAME = os.getenv("INSTA_USERNAME")
    INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
    TEMP_DIR = "temp_files"  # For videos, audio, frames
    LOG_LEVEL = logging.INFO

    @staticmethod
    def validate():
        if not all([Config.INSTA_USERNAME, Config.INSTA_PASSWORD, Config.GOOGLE_API_KEY, Config.MONGO_URI]):
            raise ValueError("Missing required env vars in .env")

# Setup logging
logging.basicConfig(level=Config.LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create temp dir
os.makedirs(Config.TEMP_DIR, exist_ok=True)