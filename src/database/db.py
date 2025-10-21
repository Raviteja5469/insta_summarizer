from pymongo import MongoClient, ASCENDING, ReturnDocument, UpdateOne
from pymongo.errors import OperationFailure
from datetime import datetime, timezone
from typing import Optional, List, Dict
from src.config import logger, Config
from src.database.schemas import ContentItemSchema


class Database:
    """
    Handles all interactions with MongoDB for the content pipeline.
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
            logger.info("✅ Database connection established and indexes ensured.")
        return cls._instance

    def _create_indexes(self):
        self.channels.create_index([("is_active", ASCENDING)])
        self.content_items.create_index([("status", ASCENDING), ("added_at", ASCENDING)])
        self.content_items.create_index([("channel_username", ASCENDING)])
        try:
            # _id already has a unique index by MongoDB; creating one with unique=True can fail on some servers.
            self.content_items.create_index([("_id", ASCENDING)], unique=True)
        except OperationFailure as e:
            # Ignore the specific invalid-index-spec error for _id and continue
            if "not valid for an _id index" in str(e) or getattr(e, "code", None) == 197:
                logger.debug("Skipped creating unique index on _id: default _id index already exists.")
            else:
                raise
    # ---------------------------------
    # Channel Management
    # ---------------------------------
    def get_due_channels(self) -> List[Dict]:
        """Gets all active channels due for a check."""
        now = datetime.utcnow()
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

    def update_channel_after_fetch(self, channel_id: str, last_shortcode: str):
        """Update channel with last fetch info."""
        self.channels.update_one(
            {"_id": channel_id},
            {"$set": {
                "last_checked_at": datetime.utcnow(),
                "last_fetched_shortcode": last_shortcode
            }}
        )

    def mark_channel_checked(self, username: str):
        self.channels.update_one(
            {"_id": username},
            {"$set": {"last_checked_at": datetime.utcnow()}}
        )

    # ---------------------------------
    # Content Items (Queue)
    # ---------------------------------
    def add_content_items(self, items: List[ContentItemSchema]) -> int:
        """Bulk insert content items if not already existing."""
        if not items:
            return 0

        operations = [
            UpdateOne(
                {"_id": item._id},
                {"$setOnInsert": item.dict()},
                upsert=True
            )
            for item in items
        ]

        result = self.content_items.bulk_write(operations, ordered=False)
        inserted = result.upserted_count
        logger.info(f"🆕 Added {inserted} new content items.")
        return inserted

    def add_to_queue(self, source_url: str, channel_username: str, shortcode: str):
        """Add a single item if not already in DB."""
        exists = self.content_items.find_one({"_id": shortcode})
        if exists:
            return False
        item = ContentItemSchema(
            _id=shortcode,
            source_url=source_url,
            channel_username=channel_username
        )
        self.content_items.insert_one(item.dict())
        return True

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
