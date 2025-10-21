import time
import random
import instaloader
from src.database.db import Database
from src.database.schemas import ContentItemSchema
from src.config import logger, Config
from src.auth.insta_auth import get_authenticated_loader
from instaloader.exceptions import (
    ConnectionException,
    LoginRequiredException,
)

def bootstrap_channel(username: str, limit: int = None, max_retries: int = 3):
    """
    Scrapes posts from an Instagram profile with built-in delays and retries
    to avoid rate-limiting.
    """
    db = Database()

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    )

    # This will now force a new login since you deleted the session file
    get_authenticated_loader(loader)

    # --- KEY CHANGE: LONGER "WARM-UP" DELAY ---
    # After a fresh login, wait a significant amount of time before making
    # the first request. This is crucial for avoiding immediate flags.
    warm_up_time = random.uniform(25, 40)
    logger.info(f"Login successful. Warming up session for {warm_up_time:.2f} seconds...")
    time.sleep(warm_up_time)
    # --- END KEY CHANGE ---

    profile = None
    logger.info(f"Attempting to fetch profile for username: '{username}'")
    for attempt in range(1, max_retries + 1):
        try:
            profile = instaloader.Profile.from_username(loader.context, username)
            logger.info(f"✅ Successfully fetched profile for '{username}'.")
            break
        except ConnectionException as e:
            msg = str(e)
            logger.warning(f"Connection error while fetching profile '{username}': {msg}")
            
            if "401" in msg or "Please wait a few minutes" in msg:
                logger.error(
                    "Instagram is rate-limiting the account. This is a server-side block."
                )
                # Increase the wait time even more for subsequent retries
                wait = 30 * attempt
            else:
                wait = 5 * attempt
            
            if attempt < max_retries:
                logger.info(f"Retrying in {wait}s ({attempt}/{max_retries})...")
                time.sleep(wait)
            else:
                logger.error("Failed to fetch Instagram profile after multiple retries.")
                return
        except LoginRequiredException:
            logger.error("Session became invalid. Please delete the session file and log in again.")
            return

    if not profile:
        logger.error(f"Could not retrieve profile for {username}. Aborting.")
        return

    # The rest of the code remains the same...
    logger.info(f"Starting to fetch posts for '{username}'...")
    posts = profile.get_posts()
    count = 0
    items = []

    for post in posts:
        try:
            # ... (post fetching logic as before) ...
            shortcode = post.shortcode
            url = f"https://www.instagram.com/reel/{shortcode}/"
            items.append(
                ContentItemSchema(_id=shortcode, source_url=url, channel_username=username)
            )
            count += 1
            logger.info(f"[{count}/{limit if limit else 'all'}] Fetched post: {shortcode}")

            if limit and count >= limit:
                logger.info(f"Reached specified limit of {limit} posts.")
                break

            sleep_duration = random.uniform(5, 10)
            logger.debug(f"Waiting for {sleep_duration:.2f} seconds before fetching next post...")
            time.sleep(sleep_duration)

        except ConnectionException as e:
            logger.warning(f"Connection error while fetching a post: {e}. Skipping this post after a delay.")
            time.sleep(10)
            continue

    if not items:
        logger.warning(f"No new posts were fetched for {username}.")
        return

    added = db.add_content_items(items)
    logger.info(f"📦 Bootstrap for '{username}' complete: Found {count} posts, added {added} new items to the database.")


if __name__ == "__main__":
    usernames = ["theaifield"]
    for user in usernames:
        bootstrap_channel(user, limit=50)
        logger.info(f"Completed process for {user}. Waiting 30 seconds before next run.")
        time.sleep(30)