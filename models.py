from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class SourceRecord:
    source: str
    external_id: str
    source_url: Optional[str] = None
    fetched_at: Optional[str] = None
    raw_title: Optional[str] = None
    confidence: float = 1.0
    payload: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Event:
    id: str
    title: str
    event_type: str
    category: str
    start_date: str
    end_date: Optional[str]
    start_time: Optional[str]
    venue: str
    city: str
    region: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    official_url: Optional[str] = None
    ticket_url: Optional[str] = None
    status: str = "unknown"
    source_names: List[str] = field(default_factory=list)
    source_count: int = 1
    source_records: List[SourceRecord] = field(default_factory=list)
    verified_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    is_demo: bool = False
    data_quality: str = "verified"  # verified | partial | review
    quality_notes: List[str] = field(default_factory=list)
