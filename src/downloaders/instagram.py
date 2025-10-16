import instaloader
import time
import shutil
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from src.config import Config, logger
from src.downloaders.base import BaseDownloader


class InstagramDownloader(BaseDownloader):
    LOG_FILE = Path(Config.TEMP_DIR) / "downloaded_logs.json"

    def __init__(self):
        self.L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=True,
            quiet=False,
        )
        # self._login()
        
    def _load_log(self):
        if self.LOG_FILE.exists():
            try:
                with open(self.LOG_FILE, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()
    
    def _save_log(self, shortcodes):
        try:
            with open(self.LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(sorted(list(shortcodes)), f, indent=2)
        except Exception as e:
            logger.warning(f"Could not update download log: {e}")

    def _login(self, session_file: str = None):
        username = Config.INSTA_USERNAME
        password = Config.INSTA_PASSWORD

        if not username or not password:
            raise ValueError("Instagram credentials missing")

        safe_username = "".join(
            c for c in username if c.isalnum() or c in ("-", "_")
        ).rstrip(".-_")
        
        default_session = Path(Config.TEMP_DIR) / f"session-{safe_username}"
        session_path = Path(session_file or default_session)
        session_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Looking for session at: {session_path.resolve()}")

        if session_path.exists():
            try:
                self.L.load_session_from_file(username, str(session_path))
                logger.info(f"✅ Loaded Instagram session from {session_path.name}")
                return
            except Exception as e:
                logger.warning(f"⚠️ Failed to load session ({e}); deleting old file...")
                try:
                    session_path.unlink(missing_ok=True)
                except Exception as del_err:
                    logger.warning(f"Couldn't delete invalid session file: {del_err}")
        try:
            logger.info("No valid session found. Attempting fresh login...")
            self.L.login(username, password)
            logger.info("✅ Logged in to Instagram")
            self.L.save_session_to_file(str(session_path))
            logger.info(f"💾 Saved new session to {session_path.name}")
        except instaloader.exceptions.LoginException as e:
            logger.error(f"❌ Login failed: {e}")
            raise RuntimeError(
                "Instagram checkpoint required — open the verification link in browser, verify your account, "
                "then rerun this script."
            )

    def _extract_metadata(self, post, url: str, download_dir: Path, content_type: str):
        """Extract metadata from Instagram post and save to CSV"""
        try:
            metadata = {
                "url": url,
                "shortcode": post.shortcode,
                "username": post.owner_username,
                "upload_date": post.date.strftime("%Y-%m-%d %H:%M:%S") if post.date else "",
                "caption": post.caption or "",
                "likes": post.likes,
                "video_duration": post.video_duration if post.is_video else 0,
                "media_count": post.mediacount,
                "hashtags": ", ".join(post.caption_hashtags) if post.caption_hashtags else "",
                "post_type": content_type,
                "download_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            csv_path = download_dir / f"{post.shortcode}_metadata.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=metadata.keys())
                writer.writeheader()
                writer.writerow(metadata)

            logger.info(f"📊 Metadata saved to: {csv_path.name}")
            
            readable_path = download_dir / f"{post.shortcode}_info.txt"
            with open(readable_path, "w", encoding="utf-8") as f:
                f.write("Instagram Content Metadata\n")
                f.write("=" * 30 + "\n\n")
                f.write(f"URL: {metadata['url']}\n")
                f.write(f"Channel: @{metadata['username']}\n")
                f.write(f"Upload Date: {metadata['upload_date']}\n")
                f.write(f"Type: {metadata['post_type'].title()}\n")
                f.write(f"Likes: {metadata['likes']:,}\n")
                if metadata["hashtags"]:
                    f.write(f"Hashtags: {metadata['hashtags']}\n")
                f.write(f"\nDescription:\n{metadata['caption']}\n")

            logger.info(f"📝 Readable info saved to: {readable_path.name}")
            return csv_path

        except Exception as e:
            logger.error(f"❌ Failed to extract metadata: {e}")
            return None

    def download(self, url: str) -> Optional[Dict[str, str]]:
        is_reel = "/reel/" in url or "/reels/" in url
        is_post = "/p/" in url or "/post/" in url

        if not (is_reel or is_post):
            raise ValueError("Unsupported Instagram URL type. Must contain /reel/, /reels/, /p/, or /post/")

        content_type = "reel" if is_reel else "post"
        logger.info(f"Detected content type: {content_type}")

        shortcode = url.strip("/").split("/")[-1]
        
        downloaded = self._load_log()
        if shortcode in downloaded:
            logger.info(f"Shortcode {shortcode} already downloaded. Skipping.")
            # Return the expected object structure even for skips
            download_dir = Path(f"{Config.TEMP_DIR}/{content_type}_{shortcode}")
            return {
                "folder_path": "skip",
                "content_type": content_type
            }

        download_dir = Path(f"{Config.TEMP_DIR}/{content_type}_{shortcode}")

        if download_dir.exists():
            shutil.rmtree(download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Downloading content {shortcode} to {download_dir}")
            post = instaloader.Post.from_shortcode(self.L.context, shortcode)

            # Pass the correctly identified content_type
            self._extract_metadata(post, url, download_dir, content_type)

            old_dirname_pattern = self.L.dirname_pattern
            old_filename_pattern = self.L.filename_pattern
            
            # This logic is correct for forcing download into a specific folder
            self.L.dirname_pattern = str(download_dir)
            self.L.filename_pattern = "{shortcode}"
            
            self.L.download_post(post, target=".")
            
            self.L.dirname_pattern = old_dirname_pattern
            self.L.filename_pattern = old_filename_pattern
            
            time.sleep(1)

            # Instead of looking for a single file, we just check if *any* media was downloaded.
            # This works for both single-video reels and multi-image posts.
            media_extensions = {".mp4", ".mov", ".jpg", ".jpeg", ".png", ".webp"}
            media_files_found = any(f.suffix.lower() in media_extensions for f in download_dir.iterdir())

            if not media_files_found:
                logger.error(
                    f"No media files found after download. Directory contents: {list(download_dir.iterdir())}"
                )
                raise FileNotFoundError(f"No media files downloaded in {download_dir}")

            logger.info(f"📁 Download complete! Files saved in '{download_dir}':")
            for file in sorted(download_dir.iterdir()):
                size_kb = file.stat().st_size / 1024
                logger.info(f"  - {file.name} ({size_kb:.1f} KB)")
                
            downloaded.add(shortcode)
            self._save_log(downloaded)

            return {
                "folder_path": str(download_dir),
                "content_type": content_type
            }

        except instaloader.exceptions.LoginRequiredException:
            logger.error("Login required - re-authenticating...")
            self._login()
            return self.download(url)

        except Exception as e:
            logger.error(f"Download error: {e}")
            if download_dir.exists():
                shutil.rmtree(download_dir)
            raise RuntimeError(f"Instagram download failed: {str(e)}")