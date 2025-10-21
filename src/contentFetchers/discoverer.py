import instaloader
from datetime import datetime, timezone
from src.config import logger
from src.database.db import Database
import time

class Discoverer:
    def __init__(self):
        self.db = Database()
        logger.info("Discoverer initialized.")

        # Configure instaloader to only fetch metadata, not actual media
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True
        )

    def fetch_latest_reels(self, username, last_fetched_shortcode=None, limit=15):
        """Fetch latest reel URLs for a given username."""
        profile = instaloader.Profile.from_username(self.loader.context, username)
        posts = profile.get_posts()

        new_urls = []
        count = 0

        for post in posts:
            if count >= limit:
                break

            shortcode = post.shortcode
            if shortcode == last_fetched_shortcode:
                logger.info(f"Reached last fetched post ({shortcode}) for {username}. Stopping.")
                break

            url = f"https://www.instagram.com/reel/{shortcode}/"
            new_urls.append({
                "shortcode": shortcode,
                "url": url,
                "timestamp": post.date_utc
            })
            count += 1

        return new_urls

    def run_once(self):
        logger.info("🔍 Discoverer running: Checking for due channels...")
        due_channels = self.db.get_due_channels()

        if not due_channels:
            logger.info("No channels are due for a content check right now.")
            return

        for channel in due_channels:
            username = channel["username"]
            last_shortcode = channel.get("last_fetched_shortcode")
            logger.info(f"Fetching new reels for @{username}...")

            try:
                start_time = time.time()
                new_posts = self.fetch_latest_reels(username, last_shortcode, limit=15)

                if not new_posts:
                    logger.info(f"No new posts found for @{username}.")
                    self.db.update_channel_check_time(channel["_id"])
                    continue

                # Add new posts to DB queue
                for post in new_posts:
                    self.db.add_to_queue(
                        source_url=post["url"],
                        channel_id=channel["_id"]
                    )

                # Update channel info
                latest_shortcode = new_posts[0]["shortcode"]
                self.db.update_channel_after_fetch(
                    channel["_id"],
                    latest_shortcode
                )

                end_time = time.time()
                logger.info(f"✅ @{username}: Added {len(new_posts)} new posts in {round(end_time-start_time,2)}s")

            except Exception as e:
                logger.error(f"❌ Failed fetching for {username}: {e}", exc_info=True)
                continue

        logger.info("Discoverer run finished.")
