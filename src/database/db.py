from pymongo import MongoClient, ASCENDING, DESCENDING, ReturnDocument, UpdateOne
from datetime import datetime, timezone
from typing import Optional, List, Dict
from src.config import logger, Config
from src.database.schemas import ContentItemSchema, ChannelSchema


class Database:
    """
    Handles all interactions with MongoDB for the content pipeline.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.client = MongoClient(Config.MONGO_URI)
            try:
                cls._instance.client.admin.command("ping")
                logger.info("✅ Database ping successful.")
            except Exception as e:
                logger.warning(
                    f"⚠️ Database ping failed: {e} — connection will be retried lazily by MongoClient."
                )
            cls._instance.db = cls._instance.client["content_pipeline"]
            cls._instance.channels = cls._instance.db["channels"]
            cls._instance.content_items = cls._instance.db["content_items"]
            cls._instance._create_indexes()
            logger.info("✅ Database initialized and indexes ensured.")
        return cls._instance

    def _create_indexes(self):
        self.channels.create_index([("is_active", ASCENDING)])
        self.content_items.create_index(
            [
                ("status", ASCENDING),
                ("priority", DESCENDING),
                ("added_at", ASCENDING),
            ]
        )
        self.content_items.create_index([("channel_username", ASCENDING)])
        # Do not attempt to create a unique _id index — MongoDB provides that by default.
        logger.debug("Indexes ensured on channels and content_items collections.")

    def _dump_model(self, model):
        # Support both Pydantic v2 (model_dump) and v1 (dict)
        if hasattr(model, "model_dump"):
            return model.model_dump(by_alias=True)
        if hasattr(model, "dict"):
            return model.dict(by_alias=True)
        # Fallback: if it's already a dict
        if isinstance(model, dict):
            return model
        raise TypeError("Unsupported model type for dumping to dict.")

    def add_channel(self, channel: ChannelSchema):
        """Adds a new channel or updates an existing one."""
        channel_dict = self._dump_model(channel)
        channel_id = channel_dict.get("_id")
        if channel_id is None:
            raise ValueError("Channel object must provide an '_id' field.")

        self.channels.update_one(
            {"_id": channel_id}, {"$set": channel_dict}, upsert=True
        )
        logger.info(f"💾 Channel '{channel_id}' saved/updated.")

    def get_due_channels(self) -> List[Dict]:
        """Gets all active channels due for a check."""
        now = datetime.now(timezone.utc)
        query = {
            "is_active": True,
            "$or": [
                {"last_checked_at": None},
                {
                    "$expr": {
                        "$lte": [
                            {
                                "$dateAdd": {
                                    "startDate": "$last_checked_at",
                                    "unit": "hour",
                                    "amount": {
                                        "$ifNull": ["$fetch_frequency_hours", 6]
                                    },
                                }
                            },
                            now,
                        ]
                    }
                },
            ],
        }
        channels = list(self.channels.find(query).sort("priority", DESCENDING))
        logger.info(f"get_due_channels: found {len(channels)} due channels.")
        # Debug fallback: if none found, return all active channels for inspection
        if not channels:
            logger.warning(
                "No due channels found. Returning all active channels for debugging."
            )
            channels = list(
                self.channels.find({"is_active": True}).sort("priority", DESCENDING)
            )
        return channels

    def update_channel_after_fetch(
        self, channel_id: str, last_shortcode: Optional[str]
    ):
        """Update channel with last fetch info."""
        if last_shortcode is None:
            self.mark_channel_checked(channel_id)
            return

        self.channels.update_one(
            {"_id": channel_id},
            {
                "$set": {
                    "last_checked_at": datetime.now(timezone.utc),
                    "last_fetched_shortcode": last_shortcode,
                }
            },
        )

    def mark_channel_checked(self, channel_id: str):
        self.channels.update_one(
            {"_id": channel_id},
            {"$set": {"last_checked_at": datetime.now(timezone.utc)}},
        )

    def add_content_items(self, items: List[ContentItemSchema]) -> int:
        """Bulk insert content items if not already existing."""
        if not items:
            return 0

        operations = []
        for item in items:
            item_dict = self._dump_model(item)
            item_id = item_dict.get("_id")
            if item_id is None:
                logger.debug("Skipping content item without _id.")
                continue
            operations.append(
                UpdateOne({"_id": item_id}, {"$setOnInsert": item_dict}, upsert=True)
            )

        if not operations:
            return 0

        result = self.content_items.bulk_write(operations, ordered=False)
        inserted = getattr(result, "upserted_count", 0)
        logger.info(f"🆕 Added {inserted} new content items.")
        return inserted

    def update_channel_info(self, channel_id: str, info_dict: dict):
        """Updates a channel with rich data (followers, etc.)."""
        self.channels.update_one({"_id": channel_id}, {"$set": info_dict})
        logger.info(f"Updated @{channel_id} with new channel info.")

    def mark_channel_bootstrapped(
        self, channel_id: str, latest_shortcode: Optional[str]
    ):
        """Marks a channel as bootstrapped and sets its initial state."""
        update_data = {
            "is_bootstrapped": True,
            "last_checked_at": datetime.now(timezone.utc),
        }
        if latest_shortcode:
            update_data["last_fetched_shortcode"] = latest_shortcode

        self.channels.update_one({"_id": channel_id}, {"$set": update_data})

    def claim_pending_item(self) -> Optional[Dict]:
        return self.content_items.find_one_and_update(
            {"status": "pending"},
            {
                "$set": {
                    "status": "processing",
                    "processed_at": datetime.now(timezone.utc),
                }
            },
            sort=[("priority", DESCENDING), ("added_at", ASCENDING)],
            return_document=ReturnDocument.AFTER,
        )

    def update_item_with_metadata(self, post_id: str, metadata: Dict):
        """
        Updates a content item with metadata fields after it has been downloaded.
        This is typically called by a worker process.
        """
        self.content_items.update_one({"_id": post_id}, {"$set": metadata})
        logger.info(f"📝 Updated item '{post_id}' with metadata.")

    def complete_item(
        self, post_id: str, final_report: str, structured_data: Dict, metadata: Dict
    ):
        self.content_items.update_one(
            {"_id": post_id},
            {
                "$set": {
                    "status": "completed",
                    "final_summary_report": final_report,
                    "structured_summary": structured_data,
                    "processing_metadata": metadata,
                    "processed_at": datetime.now(timezone.utc),
                }
            },
        )

    def fail_item(self, post_id: str, error_message: str):
        self.content_items.update_one(
            {"_id": post_id},
            {"$set": {"status": "failed", "error_message": error_message}},
        )

    def get_all_channels(self) -> List[Dict]:
        """
        Returns all channels in the database.
        """
        return list(self.channels.find({}))
