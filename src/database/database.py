from pymongo import MongoClient, ASCENDING, ReturnDocument
from datetime import datetime
from typing import Optional, List, Dict
from src.config import logger, Config
from src.database.schemas import ContentItemSchema # Import schemas for type safety

class Database:
    """
    Handles all interactions with the MongoDB database for the content pipeline.
    This class is designed as a singleton pattern to ensure one connection.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.client = MongoClient(Config.MONGO_URI)
            cls._instance.db = cls._instance.client["content_pipeline"]
            cls._instance.channels = cls._instance.db["channels"]
            cls._instance.content_items = cls._instance.db["content_items"]
            cls._instance._create_indexes()
            logger.info("Database connection established and indexes ensured.")
        return cls._instance

    def _create_indexes(self):
        self.channels.create_index([("is_active", ASCENDING)])
        self.content_items.create_index([("status", ASCENDING), ("added_at", ASCENDING)])
        self.content_items.create_index([("channel_username", ASCENDING)])

    def get_due_channels(self) -> List[Dict]:
        """Gets all active channels that are due for a new content check."""
        now = datetime.utcnow()
        # Query for channels that have never been checked OR are past their next check time
        query = {
            "is_active": True,
            "$or": [
                {"last_checked_at": None},
                {"$expr": {
                    "$lte": [
                        {"$add": ["$last_checked_at", {"$multiply": ["$fetch_frequency_hours", 3600 * 1000]}]},
                        now
                    ]
                }}
            ]
        }
        return list(self.channels.find(query).sort("priority", ASCENDING))

    def mark_channel_checked(self, username: str):
        self.channels.update_one({"_id": username}, {"$set": {"last_checked_at": datetime.utcnow()}})

    def add_content_items(self, items: List[ContentItemSchema]) -> int:
        """Adds multiple content items if they don't already exist."""
        if not items:
            return 0
        from pymongo import UpdateOne
        operations = [
            UpdateOne(
                {"_id": item.get("_id")}, 
                {"$setOnInsert": item}, 
                upsert=True
            )
            for item in items
        ]
        result = self.content_items.bulk_write(operations)
        upserted_count = result.upserted_count
        logger.info(f"Bulk write complete. Added {upserted_count} new content items.")
        return upserted_count

    def claim_pending_item(self) -> Optional[Dict]:
        """Atomically finds one pending item, claims it, and returns it."""
        return self.content_items.find_one_and_update(
            {"status": "pending"},
            {"$set": {"status": "processing", "processed_at": datetime.utcnow()}},
            sort=[("added_at", ASCENDING)],
            return_document=ReturnDocument.AFTER
        )

    def complete_item(self, post_id: str, final_report: str, structured_data: Dict, metadata: Dict):
        self.content_items.update_one(
            {"_id": post_id},
            {
                "$set": {
                    "status": "completed",
                    "final_summary_report": final_report,
                    "structured_summary": structured_data,
                    "processing_metadata": metadata,
                    "processed_at": datetime.utcnow()
                }
            }
        )

    def fail_item(self, post_id: str, error_message: str):
        self.content_items.update_one(
            {"_id": post_id},
            {"$set": {"status": "failed", "error_message": error_message}}
        )