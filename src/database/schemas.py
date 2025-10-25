from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

# --- Channel Schema (Expanded) ---
class ChannelSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    platform: str = "instagram"
    is_active: bool = True

    priority: int = Field(default=1, description="Priority for fetching (1-10)")
    category: Optional[str] = None
    posts_to_fetch: int = Field(default=10, description="Number of recent posts to fetch in scheduled scrapes.")
    max_posts_to_fetch: Optional[int] = Field(default=50, description="Max posts to fetch during the initial bootstrap.")
    fetch_frequency_hours: int = Field(default=6, description="How often to re-fetch.")

    is_bootstrapped: bool = Field(default=False, description="True if the initial deep scrape is complete.")

    follower_count: Optional[int] = None
    media_count: Optional[int] = None
    biography: Optional[str] = None
    
    # --- State Tracking Fields ---
    last_checked_at: Optional[datetime] = None
    last_fetched_shortcode: Optional[str] = None


# --- Content Item and Metadata Schemas ---
class ProcessingMetadata(BaseModel):
    worker_id: Optional[str] = None
    processing_time_sec: Optional[float] = None
    model_used: Optional[str] = "gemini-1.5-flash"


class ContentItemSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")  # The post's unique shortcode
    source_url: str
    channel_username: str
    status: str = Field(default="pending", description="pending|processing|completed|failed")
    added_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    priority: int = Field(default=1, description="Copied from the channel for worker prioritization")

    upload_date: Optional[datetime] = None
    caption: Optional[str] = None
    likes: Optional[int] = None
    video_duration: Optional[float] = None
    hashtags: Optional[List[str]] = None
    post_type: Optional[str] = None # 'reel' or 'post'

    final_summary_report: Optional[str] = None
    structured_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_metadata: Optional[ProcessingMetadata] = None