# src/services/discoverer_service.py

import os
import time
import random
from instagrapi import Client
from instagrapi.types import Media, User
from typing import List, Optional, Dict, Any

from src.database.db import Database
from src.database.schemas import ContentItemSchema, ChannelSchema
from src.config import Config, logger

# --- CONFIGURATION ---
SESSION_FILE = "temp_files/session.json"
USERNAME = Config.INSTA_USERNAME
PASSWORD = Config.INSTA_PASSWORD

# --- All your helper functions go here ---
# (login_to_instagram, map_post_type, create_content_item_from_post, 
#  fetch_user_id, analyze_channel_info)

def login_to_instagram() -> Optional[Client]:
    """Logs in to Instagram using a saved session or new credentials."""
    cl = Client()
    cl.delay_range = [1, 3]

    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.get_timeline_feed()
            logger.info("✅ Reused saved Instagram session!")
            return cl
        except Exception as e:
            logger.warning(f"⚠️ Saved session invalid, logging in again. Error: {e}")

    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings(SESSION_FILE)
        logger.info("✅ Logged in successfully and session saved!")
        return cl
    except Exception as e:
        logger.error(f"❌ Failed to login to Instagram: {e}")
        return None


def map_post_type(media: Media) -> str:
    if media.media_type == 1:
        return "post"
    if media.media_type == 2 and media.product_type == "clips":
        return "reel"
    if media.media_type == 2:
        return "video"
    if media.media_type == 8:
        return "album"
    return "unknown"


def create_content_item_from_post(post: Media, channel_id: str, channel_priority: int) -> ContentItemSchema:
    hashtags = [ht.name for ht in post.caption_hashtags]
    prefix = (
        "p" if post.media_type in [1, 8]
        else "reel" 
        if (post.media_type == 2 and getattr(post, "product_type", "") == "clips")
        else "p"
    )
    return ContentItemSchema(
        id=post.code,
        source_url=f"https://www.instagram.com/{prefix}/{post.code}/",
        channel_username=channel_id,
        priority=channel_priority,
        status="pending",
        upload_date=post.taken_at,
        caption=post.caption_text,
        likes=post.like_count,
        video_duration=getattr(post, "video_duration", None),
        hashtags=hashtags,
        post_type=map_post_type(post),
    )


def fetch_user_id(cl: Client, username: str) -> Optional[str]:
    """Try multiple methods to get user_id safely"""
    try:
        user = cl.user_info_by_username(username)
        return user.pk
    except Exception:
        try:
            results = cl.search_users(username)
            if results:
                return results[0].pk
            else:
                raise Exception("User not found in search results.")
        except Exception as e:
            logger.error(f"⚠ Failed to fetch user_id for '{username}': {e}")
            return None

def analyze_channel_info(user_info: User) -> Dict[str, Any]:
    """
    Analyzes a user_info object to create a dict of "smart" fields
    to update in our database, focusing on tech, study, and job news.
    """
    smart_data = {
        "follower_count": user_info.follower_count,
        "media_count": user_info.media_count,
        "biography": user_info.biography,
        "is_active": not user_info.is_private,
    }

    # --- 1. Topic & Category Analysis ---
    base_priority = 1  # Default priority for non-relevant accounts
    category = "General"
    
    # Combine bio and username for a better search
    search_text = (user_info.biography + " " + user_info.username).lower()

    # Define keyword lists for your target niches
    tech_keywords = [
        'tech', 'software', 'developer', 'coding', 'python', 'react', 
        'javascript', 'data science', 'ai', 'ml', 'artificial intelligence', 
        'machine learning', 'cybersecurity', 'devops', 'cloud', 'programming'
    ]
    job_keywords = ['jobs', 'hiring', 'career', 'internship', 'recruiting', 'job alert']
    study_keywords = ['studygram', 'learn', 'education', 'tutorial', 'student', 'university', 'notes']
    news_keywords = ['news', 'updates', 'daily', 'breaking']

    # Assign base priority based on keywords
    if any(kw in search_text for kw in tech_keywords):
        base_priority = 6  # High base for tech
        category = "Tech"
    elif any(kw in search_text for kw in job_keywords):
        base_priority = 5  # High base for jobs
        category = "Jobs"
    elif any(kw in search_text for kw in study_keywords):
        base_priority = 4  # Medium base for study
        category = "Study"

    # Add a bonus for "news" keywords
    if any(kw in search_text for kw in news_keywords):
        base_priority += 2
        
    # --- 2. Authority & Activity Modifiers ---

    # Verification is a strong signal of authority
    if user_info.is_verified:
        base_priority = int(base_priority * 1.5) # 50% boost

    # Follower count is now a *modifier*, not the main driver
    if user_info.follower_count > 500_000:
        base_priority += 2
    elif user_info.follower_count > 100_000:
        base_priority += 1
        
    # De-prioritize inactive or new accounts (health check)
    if user_info.media_count < 50:
        base_priority = 1

    # --- 3. Finalize Smart Settings ---
    
    # Cap priority between 1 and 10
    final_priority = min(max(base_priority, 1), 10)
    smart_data["priority"] = final_priority
    smart_data["category"] = category

    # Set fetch frequency based on final priority
    if final_priority >= 8:
        smart_data["fetch_frequency_hours"] = 2  # Check high-value targets often
        smart_data["posts_to_fetch"] = 20
    elif final_priority >= 5:
        smart_data["fetch_frequency_hours"] = 6  # Check medium-value targets moderately
        smart_data["posts_to_fetch"] = 10
    else:
        smart_data["fetch_frequency_hours"] = 12 # Check low-value targets rarely
        smart_data["posts_to_fetch"] = 10
        
    return smart_data

def analyze_post_priority(post_item: ContentItemSchema) -> int:
    """
    Analyzes a newly created ContentItemSchema to adjust its priority
    based on signals for "important" content.
    """
    # Start with the channel's priority as the baseline
    new_priority = post_item.priority 

    # --- 1. Content Keyword Analysis ---
    search_text = (
        (post_item.caption or "") + " " + " ".join(post_item.hashtags or [])
    ).lower()
    
    # Keywords that signal high, timely value
    urgent_keywords = [
        'breaking', 'announcement', 'now hiring', 'urgent', 'alert', 
        'job alert', 'new post', 'important update'
    ]
    
    # Keywords that signal high-quality, evergreen content
    value_keywords = [
        'tutorial', 'guide', 'roadmap', 'free resource', 'deep dive', 
        'cheatsheet', 'interview tips'
    ]

    if any(kw in search_text for kw in urgent_keywords):
        new_priority += 3
    elif any(kw in search_text for kw in value_keywords):
        new_priority += 2

    # --- 2. Engagement Analysis ---
    # Simple check for high engagement (absolute numbers)
    if post_item.likes and post_item.likes > 20000:
        new_priority += 2  # Very high engagement
    elif post_item.likes and post_item.likes > 5000:
        new_priority += 1  # Good engagement
        
    # --- 3. Post Type Analysis ---
    # Carousels (albums) are often high-effort tutorials
    if post_item.post_type == "album":
        new_priority += 1
    # Reels can be low-effort, so slightly de-prioritize
    elif post_item.post_type == "reel":
        new_priority -= 1

    # --- 4. Finalize ---
    # Clamp the final priority between 1 (lowest) and 10 (highest)
    return min(max(new_priority, 1), 10)

class DiscovererService:
    """
    The "Scout" service. Finds new posts and queues them as 'pending' jobs.
    """
    def __init__(self):
        self.db = Database()
        self.client = login_to_instagram()

    def run_bootstrap_for_channel(self, channel: ChannelSchema):
        """
        Runs the one-time deep scrape for a new channel.
        Fetches rich data, sets smart defaults, and scrapes historical posts.
        """
        # NOTE: Pass self.client and self.db
        logger.info(f"🚀 BOOTSTRAPPING new channel: @{channel.id}")
        try:
            user_info = self.client.user_info_by_username(channel.id)
            smart_data = analyze_channel_info(user_info)
            self.db.update_channel_info(channel.id, smart_data)
            channel = channel.model_copy(update=smart_data)
            if not channel.is_active:
                logger.warning(f"Channel @{channel.id} is private. Deactivating.")
                self.db.mark_channel_bootstrapped(channel.id, None)
                return
        except Exception as e:
            logger.error(f"Failed to fetch user info for @{channel.id}. Skipping. Error: {e}")
            self.db.mark_channel_checked(channel.id)
            return

        try:
            user_id = fetch_user_id(self.client, channel.id)
            if not user_id:
                logger.error(f"Failed to fetch user_id for @{channel.id}. Skipping.")
                self.db.mark_channel_checked(channel.id)
                return

            logger.info(f"Fetching up to {channel.max_posts_to_fetch} posts for @{channel.id}...")
            medias = self.client.user_medias(user_id, channel.max_posts_to_fetch)
            
            if not medias:
                logger.info(f"No posts found for @{channel.id}.")
                self.db.mark_channel_bootstrapped(channel.id, None)
                return
            
            items_to_add: List[ContentItemSchema] = []
            for p in medias:
                # 1. Create the item 
                item = create_content_item_from_post(p, channel.id, channel.priority)

                # 2. Re-analyze and set the *post's* final priority
                item.priority = analyze_post_priority(item) 
                items_to_add.append(item)

            added_count = self.db.add_content_items(items_to_add)
            latest_shortcode = items_to_add[0].id if items_to_add else None
            self.db.mark_channel_bootstrapped(channel.id, latest_shortcode)
            logger.info(f"✅ Bootstrap complete for @{channel.id}. Added {added_count} posts.")
        except Exception as e:
            logger.error(f"Failed during bootstrap post fetch for @{channel.id}. Error: {e}")
            self.db.mark_channel_checked(channel.id)

    def run_scheduled_check(self, channel: ChannelSchema):
        """
        Runs a regular check for new posts, stopping at the last known post.
        """
        # NOTE: Pass self.client and self.db
        logger.info(f"📸 REGULAR CHECK for @{channel.id}")
        try:
            user_id = fetch_user_id(self.client, channel.id)
            if not user_id:
                logger.error(f"Failed to fetch user_id for @{channel.id}. Skipping.")
                self.db.mark_channel_checked(channel.id)
                return

            medias = self.client.user_medias(user_id, channel.posts_to_fetch)
            new_items_to_add: List[ContentItemSchema] = []
    
            for post in medias:
                if post.code == channel.last_fetched_shortcode:
                    logger.info(f"Found last fetched post ({post.code}). Stopping scrape.")
                    break
                
                # 1. Create the item
                item = create_content_item_from_post(post, channel.id, channel.priority)
                # 2. Re-analyze and set the *post's* final priority
                item.priority = analyze_post_priority(item)
                new_items_to_add.append(item)
            
            if new_items_to_add:
                added_count = self.db.add_content_items(new_items_to_add)
                latest_shortcode = new_items_to_add[0].id
                self.db.update_channel_after_fetch(channel.id, latest_shortcode)
                logger.info(f"Added {added_count} new posts for @{channel.id}.")
            else:
                self.db.mark_channel_checked(channel.id)
                logger.info(f"No new posts found for @{channel.id}.")
        except Exception as e:
            logger.error(f"❌ Error during scheduled fetch for @{channel.id}: {e}")
            self.db.mark_channel_checked(channel.id)

    def run_once(self):
        """
        This is the single function the scheduler will call.
        """
        logger.info("🚀 Starting discoverer service run...")
        
        if not self.client:
            logger.error("Stopping run: Instagram login failed.")
            return

        try:
            if Config.FORCE_CHECK_ALL:
                logger.info("⚡ FORCE_CHECK_ALL is enabled. Fetching all channels for testing.")
                channels_to_check = (self.db.get_all_channels())  
            else:
                channels_to_check = (self.db.get_due_channels())
        except Exception as e:
            logger.error(f"❌ Failed to get channels from DB: {e}")
            return

        if not channels_to_check:
            logger.info("✅ No channels are due for checking. Service run complete.")
            return

        logger.info(f"📂 Found {len(channels_to_check)} channels to process...")
        for channel_data in channels_to_check:
            try:
                channel = ChannelSchema(**channel_data)
            except Exception as e:
                logger.error(f"Invalid channel data for '{channel_data.get('_id')}'. Skipping. Error: {e}")
                continue

            # This is the "smart" logic!
            if not channel.is_bootstrapped:
                self.run_bootstrap_for_channel(channel)
            else:
                self.run_scheduled_check(channel)

            logger.info(f"--- Completed processing for @{channel.id} ---")
            time.sleep(random.uniform(5, 15))

        logger.info("\n🎉 Discoverer service run complete.")