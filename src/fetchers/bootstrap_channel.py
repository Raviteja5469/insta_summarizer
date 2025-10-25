


# not needed as discoverer can do bootstrap too


import time
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.database.db import Database
from src.database.schemas import ContentItemSchema, ChannelSchema
from src.config import logger
from utils.driver_setup import get_driver


def bootstrap_channel(channel_data: dict):
    db = Database()

    try:
        # Pydantic will correctly map the "_id" from the input dict to the 'id' field.
        channel_schema_instance = ChannelSchema(**channel_data)
        db.add_channel(channel_schema_instance)
    except Exception as e:
        logger.error(f"❌ Invalid channel data for '{channel_data.get('_id', 'N/A')}'. Error: {e}")
        return

    username = channel_data["_id"]
    scroll_limit = channel_schema_instance.max_posts_to_fetch

    # ... (The Selenium scraping logic remains unchanged) ...
    driver = get_driver()
    url = f"https://www.instagram.com/{username}/"
    logger.info(f"🚀 Bootstrapping Instagram profile: {url}")
    driver.get(url)
    time.sleep(random.uniform(5, 8))
    post_links = set()
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    logger.info(f"📜 Starting scroll for {username} (limit={scroll_limit} posts)...")
    while len(post_links) < scroll_limit:
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/reel/')]")))
            links = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/post/') or contains(@href, '/reel/')]")
            for link in links:
                if len(post_links) >= scroll_limit: break
                href = link.get_attribute("href")
                if href: post_links.add(href)
            logger.info(f"🌀 Scroll count {scroll_count + 1}: Found {len(post_links)} unique posts so far.")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(4, 7))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.info("🛑 Reached the bottom of the page. Ending scroll.")
                break
            last_height = new_height
            scroll_count += 1
        except TimeoutException:
            logger.warning("⚠️ Page did not load new posts in time. Ending scroll.")
            break
        except Exception as e:
            logger.error(f"💥 Unexpected error during scroll: {e}")
            break
    driver.quit()
    if not post_links:
        logger.warning(f"❌ No posts found for {username}. Aborting.")
        db.mark_channel_checked(username)
        return

    logger.info(f"📦 Collected {len(post_links)} post URLs for {username}. Storing in database...")
    items_to_add = []
    for href in post_links:
        try:
            shortcode = href.split("/")[-2]
            # Instantiate the schema using the 'id' field name, not '_id'.
            items_to_add.append(
                ContentItemSchema(
                    id=shortcode,
                    source_url=href,
                    channel_username=username
                )
            )
        except IndexError:
            logger.warning(f"Could not parse shortcode from URL: {href}")
            continue

    added_count = db.add_content_items(items_to_add)

    # Access the id with '.id' now, which is safe.
    latest_item_id = items_to_add[0].id if items_to_add else None
    db.update_channel_after_fetch(username, last_shortcode=latest_item_id)

    logger.info(f"✅ Bootstrap complete for {username}: {len(post_links)} total found, {added_count} new items added.")


if __name__ == "__main__":
    channels_to_bootstrap = [
        {"_id": "theaifield", "priority": 1, "max_posts_to_fetch": 80, "posts_to_fetch": 12, "fetch_frequency_hours": 6},
        {"_id": "tech_creator_xyz", "priority": 2, "max_posts_to_fetch": 50, "posts_to_fetch": 10, "fetch_frequency_hours": 12},
    ]
    for channel_info in channels_to_bootstrap:
        bootstrap_channel(channel_info)
        logger.info(f"--- Completed process for {channel_info['_id']}. Waiting before next run... ---")
        time.sleep(random.uniform(20, 40))