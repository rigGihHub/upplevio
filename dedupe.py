import re
import unicodedata
from difflib import SequenceMatcher

def normalize_text(value: str):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"\b(live|official|tickets?|biljetter|tour|202[0-9])\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())

def similarity(a: str, b: str):
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()

def duplicate_score(a, b):
    if a.start_date != b.start_date:
        return 0.0
    title = similarity(a.title,b.title)
    city_same = bool(a.city and b.city and normalize_text(a.city)==normalize_text(b.city))
    venue_same = bool(a.venue and b.venue and normalize_text(a.venue)==normalize_text(b.venue))
    score = title * 0.70
    score += 0.18 if city_same else 0
    score += 0.12 if venue_same else 0
    return min(score,1.0)

def deduplicate(events):
    merged, review = [], []
    for event in events:
        best = None
        best_score = 0.0
        for m in merged:
            s = duplicate_score(m,event)
            if s > best_score:
                best,best_score=m,s
        if best and best_score >= 0.88:
            best.source_names = sorted(set(best.source_names + event.source_names))
            best.source_count = len(best.source_names)
            best.source_records.extend(event.source_records)
            best.image_url = best.image_url or event.image_url
            best.official_url = best.official_url or event.official_url
            best.ticket_url = best.ticket_url or event.ticket_url
            best.latitude = best.latitude or event.latitude
            best.longitude = best.longitude or event.longitude
            if event.description and len(event.description) > len(best.description):
                best.description = event.description
            best.data_quality = "verified" if len(best.source_names) > 1 else best.data_quality
        else:
            if best and 0.70 <= best_score < 0.88:
                review.append((best,event,best_score))
            merged.append(event)
    return merged, review
