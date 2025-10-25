import sys
import os

# This line allows the script to find your 'src' folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.db import Database
from src.database.schemas import ChannelSchema
from src.config import logger

def add_channels(usernames: list[str]):
    """
    Adds one or more new channels to the database with default settings.
    """
    if not usernames:
        print("Error: No usernames provided.")
        print("Usage: python utils/add_new_channel.py <username1> [username2] ...")
        return

    db = Database()
    added_count = 0

    for username in usernames:
        try:
            # Create a minimal channel object.
            new_channel = ChannelSchema(id=username)
            
            # Use your existing add_channel function
            db.add_channel(new_channel)
            
            logger.info(f"✅ Successfully queued new channel: @{username}")
            added_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to add channel @{username}. Error: {e}")

    logger.info(f"--- Done. Added {added_count} new channel(s). ---")
    logger.info("The main scheduler will automatically bootstrap them on its next discoverer run.")

if __name__ == "__main__":
    # Get all arguments after the script name (e.g., "python utils/add_new_channel.py user1 user2")
    channel_names_from_args = sys.argv[1:]
    add_channels(channel_names_from_args)