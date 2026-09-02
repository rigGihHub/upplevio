from datetime import datetime, timedelta, timezone
import json
import requests
from models import Event, SourceRecord
from taxonomy import classify

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

def ticketmaster_events(api_key: str, country_code="SE", size=120):
    if not api_key:
        return []
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {"apikey": api_key,"countryCode": country_code,"size": min(size, 200),"sort": "date,asc"}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    raw = r.json().get("_embedded", {}).get("events", [])
    result = []
    for x in raw:
        dates = x.get("dates", {})
        start = dates.get("start", {})
        venue = ((x.get("_embedded") or {}).get("venues") or [{}])[0]
        classifications = x.get("classifications") or [{}]
        c0 = classifications[0] if classifications else {}
        segment = (c0.get("segment") or {}).get("name") or "Evenemang"
        genre = (c0.get("genre") or {}).get("name") or segment
        event_type = "Konsert" if segment.lower() == "music" else "Evenemang"
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
            image_url=image_url,official_url=x.get("url"),ticket_url=x.get("url"),
            status=((dates.get("status") or {}).get("code") or "unknown"),
            source_names=["Ticketmaster"],source_count=1,
            source_records=[SourceRecord(source="Ticketmaster", external_id=ext_id, source_url=x.get("url"), fetched_at=_now_iso(), raw_title=x.get("name"))],
            verified_at=_now_iso(),created_at=_now_iso(),updated_at=_now_iso(),
            description=(x.get("info") or x.get("pleaseNote") or ""),
            tags=[segment,genre],is_demo=False,data_quality="verified"
        ))
    return result

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

def visitsweden_events(limit=100, offset=0):
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
            id=f"vs-{abs(hash(ext_id))}", title=title,event_type=type_text,category="Okategoriserat",
            start_date=start_date,end_date=str(end)[:10] if end else None,start_time=None,
            venue=venue,city=city,region=region,country="Sverige",
            latitude=lat,longitude=lon,image_url=None,official_url=url_value,ticket_url=None,
            status="confirmed",source_names=["Visit Sweden"],source_count=1,
            source_records=[SourceRecord(source="Visit Sweden",external_id=ext_id,source_url=url_value,fetched_at=_now_iso(),raw_title=title)],
            verified_at=_now_iso(),created_at=_now_iso(),updated_at=_now_iso(),
            description=desc,tags=[],is_demo=False,
            data_quality="partial",quality_notes=["Kategori normaliseras konservativt från Visit Sweden-data"]
        ))
    return events

def load_events(api_key=None, include_visitsweden=True, experimental_official_keys=None, experimental_collector_keys=None, experimental_entertainment_keys=None):
    events = []
    source_health = []
    if api_key:
        try:
            tm = ticketmaster_events(api_key)
            events.extend(tm)
            source_health.append(("Ticketmaster","OK",len(tm),None))
        except Exception as exc:
            source_health.append(("Ticketmaster","Fel",0,str(exc)))
    else:
        source_health.append(("Ticketmaster","Ej konfigurerad",0,"API-nyckel saknas"))

    if include_visitsweden:
        try:
            vs = visitsweden_events(limit=100)
            events.extend(vs)
            source_health.append(("Visit Sweden","OK",len(vs),None))
        except Exception as exc:
            source_health.append(("Visit Sweden","Fel",0,str(exc)))

    # Keep demo rows until real-source coverage is sufficient, always clearly marked.
    if experimental_official_keys:
        try:
            from official_sources import experimental_official_events
            extra, extra_health = experimental_official_events(experimental_official_keys)
            events.extend(extra)
            source_health.extend(extra_health)
        except Exception as exc:
            source_health.append(("Officiella mässkalendrar","Fel",0,str(exc)))

    if experimental_collector_keys:
        try:
            from collector_sources import experimental_collector_events
            extra, extra_health = experimental_collector_events(experimental_collector_keys)
            events.extend(extra)
            source_health.extend(extra_health)
        except Exception as exc:
            source_health.append(("Samlarkällor","Fel",0,str(exc)))

    if experimental_entertainment_keys:
        try:
            from entertainment_sources import experimental_entertainment_events
            extra, extra_health = experimental_entertainment_events(experimental_entertainment_keys)
            events.extend(extra); source_health.extend(extra_health)
        except Exception as exc:
            source_health.append(("Scen/underhållning","Fel",0,str(exc)))

    # Enrich every event with the common multi-label taxonomy.
    for e in events:
        cls = classify(e.title, e.description, e.event_type, e.category)
        e.event_type = cls.event_type
        e.category = cls.category
        e.tags = sorted(set(e.tags + cls.tags))

    events.extend(demo_events())
    source_health.append(("Demo","OK",10,"Endast UX-testdata"))
    return events, source_health
