import time
import instaloader
from src.database.db import Database
from src.database.schemas import ContentItemSchema
from src.config import logger, Config
from src.auth.insta_auth import get_authenticated_loader  # <-- Import the new function
from instaloader.exceptions import (
    ConnectionException,
    LoginRequiredException,
)

def bootstrap_channel(username: str, limit: int = None, max_retries: int = 3):
    db = Database()
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )

    # --- REFACTORED PART ---
    # The complex login logic is now replaced with a single function call.
    get_authenticated_loader(loader)
    # --- END REFACTORED PART ---

    # Small pause after login/load to reduce immediate-rate triggers
    time.sleep(2)

    # Fetch profile with retry/backoff to handle transient 401/rate-limit responses
    profile = None
    for attempt in range(1, max_retries + 1):
        try:
            profile = instaloader.Profile.from_username(loader.context, username)
            break
        except ConnectionException as e:
            msg = str(e)
            logger.warning(
                f"Connection/HTTP error while fetching profile '{username}': {msg}"
            )
            if "Please wait a few minutes" in msg or "rate-limit" in msg.lower():
                logger.warning(
                    "Instagram returned a temporary throttle (401, 'Please wait a few minutes'). "
                    "This is server-side. Wait a few minutes, reduce request frequency, or use a different IP/proxy."
                )
            if attempt < max_retries:
                wait = 2**attempt
                logger.info(f"Retrying in {wait}s ({attempt}/{max_retries})...")
                time.sleep(wait)
            else:
                raise RuntimeError(
                    "Failed to fetch Instagram profile after retries. Instagram returned a 401/ratelimit response. "
                    "Try again later, verify the account/challenge in a browser, or use a proxy/rotate IP."
                ) from e
        except LoginRequiredException:
            raise RuntimeError(
                "Instagram requires login to access this profile. Ensure credentials are set and "
                "complete any checkpoint verification if prompted."
            )

    if not profile:
        logger.error(f"Could not retrieve profile for {username}. Aborting.")
        return

    posts = profile.get_posts()
    count = 0
    items = []

    for post in posts:
        shortcode = post.shortcode
        url = f"https://www.instagram.com/reel/{shortcode}/"
        items.append(
            ContentItemSchema(_id=shortcode, source_url=url, channel_username=username)
        )
        count += 1
        if limit and count >= limit:
            break

    added = db.add_content_items(items)
    logger.info(f"📦 Bootstrapped {username}: Found {count}, added {added} new posts.")


if __name__ == "__main__":
    usernames = ["theaifield"]
    for user in usernames:
        bootstrap_channel(user)