from datetime import datetime, timedelta, timezone
import json
import hashlib
import requests
from models import Event, SourceRecord
from taxonomy import classify
from source_health import safe_import_error

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def demo_events():
    now = datetime.now()
    rows = [
        ("demo-1","Nordic Tech Expo","Mässa","Teknik",18,"Stockholmsmässan","Stockholm","Stockholm","B2B · Teknik · Innovation"),
        ("demo-2","Scandinavian Card Show","Mässa","Samlarobjekt",27,"Mässhallen","Örebro","Örebro","Samlarkort · Hobby · B2C"),
        ("demo-3","Northern Lights Festival","Festival","Rock",42,"Festivalområdet","Göteborg","Västra Götaland","Rock · Festival"),
        ("demo-4","Green Industry Forum","Mässa","Miljö & hållbarhet",66,"Conventum","Örebro","Örebro","Miljö · Avfall · B2B"),
        ("demo-5","Arena Live: The Midnight","Konsert","Rock",12,"Annexet","Stockholm","Stockholm","Rock · Internationellt"),
        ("demo-6","Gaming & Comic Weekend","Mässa","Gaming",84,"Malmömässan","Malmö","Skåne","Gaming · Comic · Anime"),
        ("demo-7","Industrial Future Days","Mässa","Industri",104,"Elmia","Jönköping","Jönköping","Industri · Tillverkning · B2B"),
        ("demo-8","Jazz by the River","Konsert","Jazz",7,"Kulturkvarteret","Örebro","Örebro","Jazz · Musik"),
        ("demo-9","Nordic Mobility Expo","Mässa","Fordon",132,"Svenska Mässan","Göteborg","Västra Götaland","Fordon · Mobilitet"),
        ("demo-10","Electronic Nights","Konsert","Elektroniskt",21,"Fållan","Stockholm","Stockholm","Elektroniskt · Klubb"),
    ]
    events = []
    for i,(eid,title,etype,cat,days,venue,city,region,tags) in enumerate(rows):
        d = now + timedelta(days=days)
        created = now - timedelta(days=(i % 5))
        events.append(Event(
            id=eid,title=title,event_type=etype,category=cat,
            start_date=d.date().isoformat(),end_date=None,start_time="19:00" if etype=="Konsert" else None,
            venue=venue,city=city,region=region,country="Sverige",
            image_url=None,official_url=None,ticket_url=None,status="confirmed",
            source_names=["Demo"],source_count=1,verified_at=_now_iso(),
            created_at=created.replace(tzinfo=timezone.utc).isoformat(),updated_at=_now_iso(),
            description=f"Demoevenemang för att visa appens MVP. {tags}.",
            tags=[t.strip() for t in tags.split("·")],is_demo=True,
            data_quality="partial",quality_notes=["Demodata – inte ett verifierat verkligt evenemang"]
        ))
    return events

def ticketmaster_events(api_key: str, country_code="SE", page_size=200, max_pages=5):
    """Fetch Ticketmaster pages conservatively and return events + import metadata."""
    if not api_key:
        return [], {"pages_fetched": 0, "page_size": page_size, "total_pages": 0, "total_elements": 0, "truncated": False}
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    page_size = min(max(int(page_size), 1), 200)
    max_pages = min(max(int(max_pages), 1), 20)
    result = []
    total_pages = None
    total_elements = None
    pages_fetched = 0
    for page in range(max_pages):
        params = {"apikey": api_key,"countryCode": country_code,"size": page_size,"page": page,"sort": "date,asc"}
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        payload = r.json()
        raw = payload.get("_embedded", {}).get("events", [])
        page_meta = payload.get("page") or {}
        if total_pages is None:
            total_pages = page_meta.get("totalPages")
            total_elements = page_meta.get("totalElements")
        pages_fetched += 1
        for x in raw:
            dates = x.get("dates", {})
            start = dates.get("start", {})
            venue = ((x.get("_embedded") or {}).get("venues") or [{}])[0]
            classifications = x.get("classifications") or [{}]
            c0 = classifications[0] if classifications else {}
            segment = (c0.get("segment") or {}).get("name") or "Evenemang"
            genre = (c0.get("genre") or {}).get("name") or segment
            event_type = "Konsert" if segment.lower() == "music" else "Evenemang"
            price_ranges = x.get("priceRanges") or []
            price_min = price_max = None
            currency = "SEK"
            price_status = "unknown"
            if price_ranges:
                pr = price_ranges[0] or {}
                price_min = _float(pr.get("min"))
                price_max = _float(pr.get("max"))
                currency = pr.get("currency") or "SEK"
                if price_min is not None:
                    price_status = "free" if price_min <= 0 and (price_max is None or price_max <= 0) else "known"
            images = x.get("images") or []
            image_url = sorted(images, key=lambda im: im.get("width", 0), reverse=True)[0].get("url") if images else None
            city = (venue.get("city") or {}).get("name") or ""
            region = (venue.get("state") or {}).get("name") or ""
            location = venue.get("location") or {}
            ext_id = x.get("id") or ""
            result.append(Event(
                id=f"tm-{ext_id}", title=x.get("name") or "Okänt evenemang",
                event_type=event_type, category=genre,
                start_date=start.get("localDate") or "", end_date=None,start_time=start.get("localTime"),
                venue=venue.get("name") or "",city=city,region=region,
                country=((venue.get("country") or {}).get("name") or "Sverige"),
                latitude=_float(location.get("latitude")), longitude=_float(location.get("longitude")),
                venue_latitude=_float(location.get("latitude")), venue_longitude=_float(location.get("longitude")),
                image_url=image_url,official_url=x.get("url"),ticket_url=x.get("url"),
                status=((dates.get("status") or {}).get("code") or "unknown"),
                source_names=["Ticketmaster"],source_count=1,
                source_records=[SourceRecord(source="Ticketmaster", external_id=ext_id, source_url=x.get("url"), fetched_at=_now_iso(), raw_title=x.get("name"))],
                verified_at=_now_iso(),created_at=_now_iso(),updated_at=_now_iso(),
                description=(x.get("info") or x.get("pleaseNote") or ""),
                tags=[segment,genre],is_demo=False,data_quality="verified",
                price_min=price_min, price_max=price_max, currency=currency, price_status=price_status
            ))
        if not raw:
            break
        if total_pages is not None and page + 1 >= int(total_pages):
            break
        if len(raw) < page_size and total_pages is None:
            break
    truncated = bool(total_pages is not None and pages_fetched < int(total_pages))
    return result, {
        "pages_fetched": pages_fetched,
        "page_size": page_size,
        "total_pages": int(total_pages or pages_fetched),
        "total_elements": int(total_elements or len(result)),
        "truncated": truncated,
    }

def _float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def _first_value(obj, keys):
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            value = obj.get(k)
            if isinstance(value, list):
                return value[0] if value else None
            return value
    return None

def _lang_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        # JSON-LD may use language-tagged values
        for item in value:
            if isinstance(item, dict) and item.get("@value"):
                if item.get("@language") in ("sv","se","en",None):
                    return item.get("@value")
        if value:
            return _lang_text(value[0])
    if isinstance(value, dict):
        return value.get("@value") or value.get("name")
    return None

def _flatten_jsonld_graph(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("@graph","results","entries"):
        if isinstance(payload.get(key), list):
            return payload[key]
    return [payload]

def _visitsweden_page(limit=100, offset=0):
    """
    Public Visit Sweden search. No key required.
    Adapter is deliberately defensive because linked-data payloads may contain
    provider-specific nesting. Records without a usable title/date are discarded.
    """
    url = "https://data.visitsweden.com/store/search"
    query = r"public:true AND rdfType:http\://schema.org/Event"
    params = {
        "type": "solr",
        "query": query,
        "limit": min(max(limit, 1), 100),
        "offset": max(offset, 0),
        "rdfFormat": "application/ld+json",
    }
    r = requests.get(url, params=params, timeout=25, headers={"Accept":"application/ld+json"})
    r.raise_for_status()
    payload = r.json()
    candidates = _flatten_jsonld_graph(payload)
    events = []
    for i, x in enumerate(candidates):
        if not isinstance(x, dict):
            continue
        title = _lang_text(_first_value(x, ["http://schema.org/name","name","schema:name"]))
        start = _lang_text(_first_value(x, ["http://schema.org/startDate","startDate","schema:startDate"]))
        if not title or not start:
            continue
        start_date = str(start)[:10]
        end = _lang_text(_first_value(x, ["http://schema.org/endDate","endDate","schema:endDate"]))
        desc = _lang_text(_first_value(x, ["http://schema.org/description","description","schema:description"])) or ""
        url_value = _lang_text(_first_value(x, ["http://schema.org/url","url","schema:url"]))
        location = _first_value(x, ["http://schema.org/location","location","schema:location"])
        venue = city = region = ""
        lat = lon = None
        if isinstance(location, dict):
            venue = _lang_text(location.get("name") or location.get("http://schema.org/name")) or ""
            address = location.get("address") or location.get("http://schema.org/address")
            if isinstance(address, dict):
                city = _lang_text(address.get("addressLocality") or address.get("http://schema.org/addressLocality")) or ""
                region = _lang_text(address.get("addressRegion") or address.get("http://schema.org/addressRegion")) or ""
            geo = location.get("geo") or location.get("http://schema.org/geo")
            if isinstance(geo, dict):
                lat = _float(geo.get("latitude") or geo.get("http://schema.org/latitude"))
                lon = _float(geo.get("longitude") or geo.get("http://schema.org/longitude"))
        ext_id = str(x.get("@id") or x.get("id") or f"offset-{offset+i}")
        type_text = "Evenemang"
        # Conservative classification. Better category mapping is a later layer.
        lower = f"{title} {desc}".lower()
        if any(w in lower for w in ["mässa","expo","fair","trade show"]):
            type_text = "Mässa"
        elif any(w in lower for w in ["konsert","concert","live music"]):
            type_text = "Konsert"
        elif "festival" in lower:
            type_text = "Festival"
        events.append(Event(
            id=f"vs-{hashlib.sha1(ext_id.encode("utf-8")).hexdigest()[:20]}", title=title,event_type=type_text,category="Okategoriserat",
            start_date=start_date,end_date=str(end)[:10] if end else None,start_time=None,
            venue=venue,city=city,region=region,country="Sverige",
            latitude=lat,longitude=lon,venue_latitude=lat,venue_longitude=lon,image_url=None,official_url=url_value,ticket_url=None,
            status="confirmed",source_names=["Visit Sweden"],source_count=1,
            source_records=[SourceRecord(source="Visit Sweden",external_id=ext_id,source_url=url_value,fetched_at=_now_iso(),raw_title=title)],
            verified_at=_now_iso(),created_at=_now_iso(),updated_at=_now_iso(),
            description=desc,tags=[],is_demo=False,
            data_quality="partial",quality_notes=["Kategori normaliseras konservativt från Visit Sweden-data"]
        ))
    return events, len(candidates)


def visitsweden_events(page_size=100, max_pages=5):
    """Fetch several Visit Sweden pages and stop honestly at a safety limit."""
    page_size = min(max(int(page_size), 1), 100)
    max_pages = min(max(int(max_pages), 1), 20)
    events = []
    pages_fetched = 0
    full_last_page = False
    for page in range(max_pages):
        offset = page * page_size
        batch, raw_count = _visitsweden_page(limit=page_size, offset=offset)
        pages_fetched += 1
        events.extend(batch)
        # Stop based on raw records, not parsed/usable records. Otherwise a malformed
        # item could make us stop before later valid pages have been inspected.
        if raw_count < page_size:
            full_last_page = False
            break
        full_last_page = True
    truncated = bool(full_last_page and pages_fetched >= max_pages)
    return events, {
        "pages_fetched": pages_fetched,
        "page_size": page_size,
        "total_pages": None,
        "total_elements": None,
        "truncated": truncated,
    }

def load_events(api_key=None, include_visitsweden=True, include_conventum=True, include_visitorebro_editorial=True, include_orebro_sports=True, include_lov_orebro=True, experimental_official_keys=None, experimental_collector_keys=None, experimental_entertainment_keys=None, include_demo=False):
    """Load independent sources concurrently while isolating source failures."""
    from source_fetch import SourceTask, run_source_tasks

    events = []
    source_health = []
    tasks = []

    if api_key:
        def fetch_ticketmaster():
            tm, meta = ticketmaster_events(api_key)
            status = "Delvis" if meta["truncated"] else "OK"
            comment = f'{meta["pages_fetched"]} sida/sidor · API-total {meta["total_elements"]}'
            if meta["truncated"]:
                comment += f' · import stoppad vid säkerhetsgräns ({meta["pages_fetched"] * meta["page_size"]} poster)'
            return tm, [("Ticketmaster", status, len(tm), comment)]
        tasks.append(SourceTask("ticketmaster", "Ticketmaster", fetch_ticketmaster))
    else:
        source_health.append(("Ticketmaster", "Ej konfigurerad", 0, "API-nyckel saknas"))

    if include_visitsweden:
        def fetch_visitsweden():
            vs, meta = visitsweden_events()
            status = "Delvis" if meta["truncated"] else "OK"
            comment = f'{meta["pages_fetched"]} sida/sidor'
            if meta["truncated"]:
                comment += f' · import stoppad vid säkerhetsgräns ({meta["pages_fetched"] * meta["page_size"]} poster)'
            return vs, [("Visit Sweden", status, len(vs), comment)]
        tasks.append(SourceTask("visitsweden", "Visit Sweden", fetch_visitsweden))

    if include_conventum:
        def fetch_conventum():
            from official_sources import conventum_events
            rows = conventum_events()
            return rows, [("Conventum", "OK", len(rows), "Officiell Örebro-kalender · lokal pilotkälla")]
        tasks.append(SourceTask("conventum", "Conventum", fetch_conventum))

    if include_visitorebro_editorial:
        def fetch_visitorebro():
            from official_sources import visitorebro_editorial_events
            rows = visitorebro_editorial_events()
            return rows, [("Visit Örebro", "OK", len(rows), "Officiella redaktionella eventlistor · kompletterande lokal discovery-källa")]
        tasks.append(SourceTask("visitorebro", "Visit Örebro", fetch_visitorebro))

    if include_lov_orebro:
        def fetch_lov_orebro():
            from community_sources import lov_orebro_events
            rows = lov_orebro_events()
            status = "OK" if rows else "Säsongstom"
            return rows, [("Lov Örebro", status, len(rows), "Officiell kommunal lovkalender · barn, unga och lokala föreningsaktiviteter")]
        tasks.append(SourceTask("lov_orebro", "Lov Örebro", fetch_lov_orebro))

    if include_orebro_sports:
        def fetch_osk():
            from sports_sources import osk_events
            rows = osk_events()
            return rows, [("ÖSK Fotboll", "OK", len(rows), "Officiella herr- och damscheman · endast hemmamatcher i Örebro")]
        def fetch_orebro_hockey():
            from sports_sources import orebro_hockey_events
            rows = orebro_hockey_events()
            return rows, [("Örebro Hockey", "Pilot", len(rows), "Officiellt publicerat spelschema · hemmamatcher i Behrn Arena")]
        tasks.extend([
            SourceTask("osk", "ÖSK Fotboll", fetch_osk),
            SourceTask("orebro_hockey", "Örebro Hockey", fetch_orebro_hockey),
        ])

    if experimental_official_keys:
        def fetch_experimental_official():
            from official_sources import experimental_official_events
            return experimental_official_events(experimental_official_keys)
        tasks.append(SourceTask("experimental_official", "Officiella mässkalendrar", fetch_experimental_official))

    if experimental_collector_keys:
        def fetch_collectors():
            from collector_sources import experimental_collector_events
            return experimental_collector_events(experimental_collector_keys)
        tasks.append(SourceTask("collectors", "Samlarkällor", fetch_collectors))

    if experimental_entertainment_keys:
        def fetch_entertainment():
            from entertainment_sources import experimental_entertainment_events
            return experimental_entertainment_events(experimental_entertainment_keys)
        tasks.append(SourceTask("entertainment", "Scen/underhållning", fetch_entertainment))

    for result in run_source_tasks(tasks):
        events.extend(result.events)
        source_health.extend(result.health)

    # Enrich every event with the common multi-label taxonomy.
    for e in events:
        cls = classify(e.title, e.description, e.event_type, e.category)
        e.event_type = cls.event_type
        e.category = cls.category
        e.tags = sorted(set(e.tags + cls.tags))

    # Production-safe default: fictitious demo events must never leak into normal results.
    # They can be explicitly enabled for local UX testing.
    if include_demo:
        demos = demo_events()
        events.extend(demos)
        source_health.append(("Demo", "TESTLÄGE", len(demos), "Fiktiv UX-testdata – visas endast när demoläge uttryckligen aktiverats"))
    return events, source_health
