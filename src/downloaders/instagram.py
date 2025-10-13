import instaloader
import time
import os
import shutil
from glob import glob
from pathlib import Path
from src.config import Config, logger
from src.downloaders.base import BaseDownloader

class InstagramDownloader(BaseDownloader):
    def __init__(self):
        self.L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            quiet=False  # Set to True in production
        )
        self._login()

    def _login(self, session_file: str = None):
        username = Config.INSTA_USERNAME
        password = Config.INSTA_PASSWORD
        if not username or not password:
            raise ValueError("Instagram credentials missing")

        # Sanitize username for filename
        safe_username = "".join(c for c in username if c.isalnum() or c in ('-', '_')).rstrip('.-_')
        session_path = Path(session_file or f"{Config.TEMP_DIR}/session-{safe_username}")
        
        # Ensure temp dir exists
        session_path.parent.mkdir(parents=True, exist_ok=True)
        
        if session_path.exists():
            try:
                self.L.load_session_from_file(username, str(session_path))
                logger.info("Loaded Instagram session")
                return
            except Exception as e:
                logger.warning(f"Failed to load session: {e}")

        self.L.login(username, password)
        logger.info("Logged in to Instagram")
        try:
            self.L.save_session_to_file(str(session_path))
            logger.info("Saved Instagram session")
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")

    def download(self, url: str) -> str:
        is_reel = '/reel/' in url
        is_post = '/p/' in url
        if not (is_reel or is_post):
            raise ValueError("Unsupported Instagram URL type. Must contain /reel/ or /p/")

        logger.info(f"Detected as {'reel' if is_reel else 'post'}")

        shortcode = url.strip("/").split("/")[-1]
        download_dir = Path(f"{Config.TEMP_DIR}/{'reel' if is_reel else 'post'}_{shortcode}")
        
        # Start fresh
        if download_dir.exists():
            shutil.rmtree(download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Downloading content {shortcode} to {download_dir}")
            post = instaloader.Post.from_shortcode(self.L.context, shortcode)

            # --- 👇 Force Instaloader to write directly into download_dir ---
            old_dirname_pattern = self.L.dirname_pattern
            self.L.dirname_pattern = str(download_dir)  # disable subfolder creation

            self.L.download_post(post, target='.')  # '.' uses our forced pattern
            self.L.dirname_pattern = old_dirname_pattern  # restore original

            # --- Optional: small cleanup delay ---
            time.sleep(1)

            # Find main media file (no recursion needed now)
            exts = ['.mp4', '.mov'] if is_reel else ['.jpg', '.png']
            candidates = [f for f in download_dir.iterdir() if f.suffix.lower() in exts]

            if not candidates:
                logger.error(f"No media files found. Directory contents: {list(download_dir.iterdir())}")
                raise FileNotFoundError(f"No media downloaded in {download_dir}")

            media_path = max(candidates, key=lambda f: f.stat().st_size)
            logger.info(f"Selected media: {media_path} ({media_path.stat().st_size / (1024 * 1024):.1f} MB)")
            return str(media_path)

        except instaloader.exceptions.LoginRequiredException:
            logger.error("Login required - re-authenticating...")
            self._login()
            return self.download(url)
        except Exception as e:
            logger.error(f"Download error: {e}")
            raise RuntimeError(f"Instagram download failed: {str(e)}")
