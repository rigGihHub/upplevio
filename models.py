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
    end_time: Optional[str] = None
    door_time: Optional[str] = None
    age_limit: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    venue_latitude: Optional[float] = None
    venue_longitude: Optional[float] = None
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
    data_quality: str = "source_verified"  # source_verified | multi_source | partial | review
    quality_notes: List[str] = field(default_factory=list)
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    currency: str = "SEK"
    price_status: str = "unknown"  # unknown | known | free
    # Commercial metadata is deliberately separate from organic discovery relevance.
    is_sponsored: bool = False
    sponsor_campaign_id: Optional[str] = None
    sponsor_company: Optional[str] = None
    sponsor_start_date: Optional[str] = None
    sponsor_end_date: Optional[str] = None
    sponsor_geo_areas: List[str] = field(default_factory=list)
    sponsor_audiences: List[str] = field(default_factory=list)
    sponsor_priority: int = 0
    booking_partner: Optional[str] = None
    booking_partner_key: Optional[str] = None
    booking_partner_domain: Optional[str] = None
    affiliate_status: str = "unassessed"
    booking_url: Optional[str] = None
    affiliate_program: Optional[str] = None
    affiliate_ref: Optional[str] = None
