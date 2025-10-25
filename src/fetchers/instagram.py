# src/fetchers/instagram_downloader.py

import instaloader
import time
import shutil
from pathlib import Path
from typing import Dict, Optional
from src.config import Config, logger
from src.fetchers.base import BaseDownloader
from src.database.db import Database

class InstagramDownloader(BaseDownloader):
    
    def __init__(self):
        self.L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,  # We already have metadata
            quiet=False,
        )
        self.db = Database()

    def download(self, job_data: Dict) -> Optional[Dict[str, str]]:
        """
        Downloads media for a job.
        All metadata and checks are now handled by the discoverer and worker.
        """
        
        # Get data directly from the job object
        try:
            shortcode = job_data["_id"]
            content_type = job_data.get("post_type", "post") # Default to "post" if missing
        except KeyError:
            raise ValueError(f"Job data is missing required fields like '_id'.")
        
        # Check if DB already has a path (from a previous failed run)
        if job_data.get("local_media_path"):
            logger.info(f"✅ Item {shortcode} already downloaded. Skipping.")
            return {
                "folder_path": job_data["local_media_path"], 
                "content_type": content_type
            }

        download_dir = Path(f"{Config.TEMP_DIR}/{content_type}_{shortcode}")

        if download_dir.exists():
            shutil.rmtree(download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Downloading content {shortcode} to {download_dir}")
            post = instaloader.Post.from_shortcode(self.L.context, shortcode)

            old_dirname_pattern = self.L.dirname_pattern
            old_filename_pattern = self.L.filename_pattern
            
            self.L.dirname_pattern = str(download_dir)
            self.L.filename_pattern = "{shortcode}"
            
            self.L.download_post(post, target=".")
            
            self.L.dirname_pattern = old_dirname_pattern
            self.L.filename_pattern = old_filename_pattern
            
            time.sleep(1)

            # Clean up non-media files
            media_extensions = {".mp4", ".mov", ".jpg", ".jpeg", ".png", ".webp"}
            media_files_found = False
            for file in download_dir.iterdir():
                if file.suffix.lower() not in media_extensions:
                    file.unlink() # Delete .txt, .json, etc.
                else:
                    media_files_found = True

            if not media_files_found:
                raise FileNotFoundError(f"No media files downloaded in {download_dir}")

            logger.info(f"📁 Download complete! Files saved in '{download_dir}':")
            for file in sorted(download_dir.iterdir()):
                size_kb = file.stat().st_size / 1024
                logger.info(f"   - {file.name} ({size_kb:.1f} KB)")
                
            # Save path to DB
            self.db.update_item_media_path(shortcode, str(download_dir))

            return {"folder_path": str(download_dir), "content_type": content_type}

        except instaloader.exceptions.LoginRequiredException:
            logger.error("Instaloader login required. Please re-login.")
            raise RuntimeError("Instagram login required by Instaloader.")

        except Exception as e:
            logger.error(f"Download error: {e}")
            if download_dir.exists():
                shutil.rmtree(download_dir)
            raise RuntimeError(f"Instagram download failed: {str(e)}")