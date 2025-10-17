from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ChannelSchema(BaseModel):
    _id: str  # The channel's unique username
    platform: str = "instagram"
    last_checked_at: Optional[datetime] = None
    fetch_frequency_hours: int = 6
    is_active: bool = True
    priority: int = 1 # Lower is higher priority

class ProcessingMetadata(BaseModel):
    worker_id: Optional[str] = None
    processing_time_sec: Optional[float] = None
    model_used: Optional[str] = "gemini-2.5-flash"

    
class ContentItemSchema(BaseModel):
    _id: str  # The post's shortcode
    source_url: str
    channel_username: str
    status: str = Field(default="pending", description="pending|processing|completed|failed")
    added_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # STORES THE FULL MARKDOWN TEXT
    final_summary_report: Optional[str] = None
    
    # STORES THE PARSED, STRUCTURED DATA
    structured_summary: Optional[Dict[str, Any]] = None
    
    error_message: Optional[str] = None
    processing_metadata: Optional[ProcessingMetadata] = None