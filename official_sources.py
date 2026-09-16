from datetime import datetime, timezone, date
import re
import hashlib
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from models import Event, SourceRecord
from source_registry import source_by_key

SV_MONTHS = {
    "jan":1,"januari":1,"feb":2,"februari":2,"mar":3,"mars":3,"apr":4,"april":4,
    "maj":5,"jun":6,"juni":6,"jul":7,"juli":7,"aug":8,"augusti":8,
    "sep":9,"september":9,"okt":10,"oktober":10,"nov":11,"november":11,"dec":12,"december":12
}

def _now():
    return datetime.now(timezone.utc).isoformat()

def _parse_swedish_range(text: str, default_year=None):
    """
    Supports common official-calendar forms:
    '9 - 13 sep. 2026', '30 sep. - 1 okt. 2026', '3 november 2026',
    '26 › 27 SEP 2026'.
    """
    if not text:
        return None, None
    clean = re.sub(r"\s+", " ", text.lower().replace("›","-").replace("–","-").replace("—","-")).strip()
    clean = clean.replace(".", "")
    year_match = re.search(r"\b(20\d{2})\b", clean)
    year = int(year_match.group(1)) if year_match else (default_year or datetime.now().year)
    work = re.sub(r"\b20\d{2}\b", "", clean).strip()

    # 30 sep - 1 okt
    m = re.search(r"(\d{1,2})\s+([a-zåäö]+)\s*-\s*(\d{1,2})\s+([a-zåäö]+)", work)
    if m:
        d1,mo1,d2,mo2=int(m.group(1)),m.group(2),int(m.group(3)),m.group(4)
        if mo1 in SV_MONTHS and mo2 in SV_MONTHS:
            return f"{year:04d}-{SV_MONTHS[mo1]:02d}-{d1:02d}", f"{year:04d}-{SV_MONTHS[mo2]:02d}-{d2:02d}"

    # 9 - 13 sep
    m = re.search(r"(\d{1,2})\s*-\s*(\d{1,2})\s+([a-zåäö]+)", work)
    if m and m.group(3) in SV_MONTHS:
        d1,d2,mo=int(m.group(1)),int(m.group(2)),SV_MONTHS[m.group(3)]
        return f"{year:04d}-{mo:02d}-{d1:02d}", f"{year:04d}-{mo:02d}-{d2:02d}"

    # 3 november
    m = re.search(r"(\d{1,2})\s+([a-zåäö]+)", work)
    if m and m.group(2) in SV_MONTHS:
        d,mo=int(m.group(1)),SV_MONTHS[m.group(2)]
        iso=f"{year:04d}-{mo:02d}-{d:02d}"
        return iso, iso

    return None, None

def _guess_type(title, description):
    text=f"{title} {description}".lower()
    if any(w in text for w in ["fackmässa","publikmässa","mässa","expo","trade fair"]):
        return "Mässa"
    if "festival" in text:
        return "Festival"
    if any(w in text for w in ["konsert","concert"]):
        return "Konsert"
    if "kongress" in text:
        return "Konferens"
    return "Evenemang"

def _event(source_key, external_id, title, date_text, venue, city, description="", url=None, category="Okategoriserat"):
    start,end=_parse_swedish_range(date_text)
    if not start:
        return None
    source=source_by_key(source_key)
    return Event(
        id=f"{source_key}-{hashlib.sha1(str(external_id).encode("utf-8")).hexdigest()[:20]}",
        title=title.strip(),event_type=_guess_type(title,description),category=category,
        start_date=start,end_date=end,start_time=None,
        venue=venue,city=city,region="",country="Sverige",
        official_url=url,status="confirmed",
        source_names=[source.name],source_count=1,
        source_records=[SourceRecord(source=source.name,external_id=external_id,source_url=url or source.url,fetched_at=_now(),raw_title=title)],
        verified_at=_now(),created_at=_now(),updated_at=_now(),
        description=description.strip(),tags=[],is_demo=False,
        data_quality="partial",
        quality_notes=["Importerad från officiell kalender med experimentell HTML-parser"]
    )

def _get(url):
    r=requests.get(url,timeout=25,headers={"User-Agent":"Upplevio/0.7 (+event discovery prototype)"})
    r.raise_for_status()
    return BeautifulSoup(r.text,"html.parser")

def stockholmsmassan_events():
    source=source_by_key("stockholmsmassan")
    soup=_get(source.url)
    events=[]
    # Deliberately broad: cards/pages change. We only accept candidates with title + date.
    for heading in soup.find_all(["h2","h3","h4"]):
        title=heading.get_text(" ",strip=True)
        if not title or len(title)>180:
            continue
        container=heading.find_parent(["article","li","div"]) or heading.parent
        text=container.get_text(" ",strip=True) if container else ""
        m=re.search(r"(\d{1,2}\s+[a-zåäö.]+(?:\s*-\s*\d{1,2}\s+[a-zåäö.]+)?\s+20\d{2}|\d{1,2}\s+[a-zåäö.]+\s*-\s*\d{1,2}\s+[a-zåäö.]+\s+20\d{2})",text,re.I)
        if not m:
            continue
        link=heading.find("a") or (container.find("a") if container else None)
        href=link.get("href") if link else None
        if href and href.startswith("/"):
            href="https://stockholmsmassan.se"+href
        e=_event("stockholmsmassan",href or title,title,m.group(1),"Stockholmsmässan","Stockholm",text,url=href)
        if e: events.append(e)
    return _unique(events)

def elmia_events():
    source=source_by_key("elmia")
    soup=_get(source.url)
    events=[]
    for heading in soup.find_all(["h2","h3","h4"]):
        title=heading.get_text(" ",strip=True)
        container=heading.find_parent(["article","li","div"]) or heading.parent
        text=container.get_text(" ",strip=True) if container else ""
        m=re.search(r"(\d{1,2}\s*-\s*\d{1,2}\s+[a-zåäö.]+\s+20\d{2}|\d{1,2}\s+[a-zåäö.]+\s*-\s*\d{1,2}\s+[a-zåäö.]+\s+20\d{2}|\d{1,2}\s+[a-zåäö.]+\s+20\d{2})",text,re.I)
        if not m:
            continue
        link=heading.find("a") or (container.find("a") if container else None)
        href=link.get("href") if link else None
        if href and href.startswith("/"):
            href="https://www.elmia.se"+href
        e=_event("elmia",href or title,title,m.group(1),"Elmia","Jönköping",text,url=href)
        if e: events.append(e)
    return _unique(events)

def malmomassan_events():
    source=source_by_key("malmomassan")
    soup=_get(source.url)
    events=[]
    # Malmömässan commonly renders a month label and day/range close to each h3.
    for heading in soup.find_all(["h2","h3","h4"]):
        title=heading.get_text(" ",strip=True)
        container=heading.find_parent(["article","li","div"]) or heading.parent
        text=container.get_text(" ",strip=True) if container else ""
        m=re.search(r"(\d{1,2}\s*-\s*\d{1,2}\s+[a-zåäö.]+\s+20\d{2}|\d{1,2}\s+[a-zåäö.]+\s+20\d{2})",text,re.I)
        if not m:
            continue
        link=heading.find("a") or (container.find("a") if container else None)
        href=link.get("href") if link else None
        e=_event("malmomassan",href or title,title,m.group(1),"Malmömässan","Malmö",text,url=href)
        if e: events.append(e)
    return _unique(events)

def _unique(events):
    seen=set()
    out=[]
    for e in events:
        key=(e.title.lower().strip(),e.start_date,e.city)
        if key in seen:
            continue
        seen.add(key);out.append(e)
    return out

def experimental_official_events(enabled_keys):
    mapping={
        "stockholmsmassan":stockholmsmassan_events,
        "elmia":elmia_events,
        "malmomassan":malmomassan_events,
    }
    events=[]
    health=[]
    for key in enabled_keys:
        fn=mapping.get(key)
        source=source_by_key(key)
        if not fn or not source:
            continue
        try:
            rows=fn()
            events.extend(rows)
            health.append((source.name,"OK (experimentell)",len(rows),"HTML-parser"))
        except Exception as exc:
            health.append((source.name,"Fel",0,str(exc)))
    return events,health


def _parse_conventum_date(text: str, today: date | None = None):
    """Parse Conventum's compact calendar dates such as 'tisdag 8/9'.

    The calendar often omits the year. We choose the next plausible occurrence,
    so a December page viewed in January cannot silently become last year's event.
    """
    if not text:
        return None
    m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(20\d{2}))?\b", text)
    if not m:
        return None
    day, month = int(m.group(1)), int(m.group(2))
    explicit_year = int(m.group(3)) if m.group(3) else None
    now = today or date.today()
    year = explicit_year or now.year
    try:
        candidate = date(year, month, day)
    except ValueError:
        return None
    if explicit_year is None and candidate < now.replace(day=1):
        # Calendar pages include future events. If month/day is clearly behind the
        # current month, interpret it as next year rather than stale data.
        try:
            candidate = date(year + 1, month, day)
        except ValueError:
            return None
    return candidate.isoformat()


def parse_conventum_html(html_text: str, today: date | None = None):
    """Parse only high-confidence event cards from Conventum's official calendar."""
    soup = BeautifulSoup(html_text or "", "html.parser")
    source = source_by_key("conventum")
    base_url = source.url if source else "https://www.conventum.se/arrangemangskalender/"
    events = []
    seen_urls = set()

    for link in soup.find_all("a", href=True):
        href = (link.get("href") or "").strip()
        if "/arrangemang/" not in href or href.rstrip("/").endswith("arrangemang"):
            continue
        absolute_url = urljoin(base_url, href)
        if absolute_url in seen_urls:
            continue
        container = link.find_parent(["article", "li", "div"])
        if container is None:
            continue
        text = container.get_text(" ", strip=True)
        start_date = _parse_conventum_date(text, today=today)
        if not start_date:
            continue
        heading = container.find(["h1", "h2", "h3", "h4"])
        title = heading.get_text(" ", strip=True) if heading else link.get_text(" ", strip=True)
        title = re.sub(r"\s+", " ", title or "").strip()
        if not title or len(title) < 3 or len(title) > 220:
            continue
        seen_urls.add(absolute_url)
        digest = hashlib.sha1(absolute_url.encode("utf-8")).hexdigest()[:20]
        events.append(Event(
            id=f"conventum-{digest}", title=title,
            event_type=_guess_type(title, text), category="Okategoriserat",
            start_date=start_date, end_date=None, start_time=None,
            venue="Conventum", city="Örebro", region="Örebro län", country="Sverige",
            official_url=absolute_url, status="confirmed",
            source_names=["Conventum"], source_count=1,
            source_records=[SourceRecord(source="Conventum", external_id=absolute_url, source_url=absolute_url, fetched_at=_now(), raw_title=title)],
            verified_at=_now(), created_at=_now(), updated_at=_now(),
            description="", tags=[], is_demo=False,
            data_quality="partial",
            quality_notes=["Datum och titel importerade från Conventums officiella arrangemangskalender", "Detaljsida har inte korsverifierats i denna import"]
        ))
    return _unique(events)


def conventum_events():
    source = source_by_key("conventum")
    soup = _get(source.url)
    rows = parse_conventum_html(str(soup))
    from booking_enrichment import enrich_events
    return enrich_events(rows, max_fetches=12, workers=6, timeout=10)

VISITOREBRO_EDITORIAL_URLS = [
    "https://www.visitorebro.se/artikel/sevart-scen-orebro/",
    "https://www.visitorebro.se/artikel/konsertsommar/",
]


def _visitorebro_year(text: str, fallback: int | None = None):
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text or "")]
    return max(years) if years else (fallback or date.today().year)


def _parse_visitorebro_date_prefix(line: str, year: int):
    if not line:
        return None
    clean = re.sub(r"\s+", " ", line.replace("–", "-").replace("—", "-")).strip()
    m = re.match(r"^(\d{1,2})/(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})\s+(.+)$", clean)
    if m:
        d1, mo1, d2, mo2, rest = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), m.group(5)
        try:
            return date(year, mo1, d1).isoformat(), date(year, mo2, d2).isoformat(), rest
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})\s+(.+)$", clean)
    if m:
        d1, d2, mo, rest = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
        try:
            return date(year, mo, d1).isoformat(), date(year, mo, d2).isoformat(), rest
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})/(\d{1,2})\s+(.+)$", clean)
    if m:
        d, mo, rest = int(m.group(1)), int(m.group(2)), m.group(3)
        try:
            iso = date(year, mo, d).isoformat()
            return iso, iso, rest
        except ValueError:
            return None
    return None


def _split_visitorebro_title_venue(rest: str):
    text = re.sub(r"\s+", " ", (rest or "")).strip(" .")
    free = bool(re.search(r"\((?:g|fri entr[eé])\)|\bfri entr[eé]\b", text, re.I))
    text = re.sub(r"\s*\((?:G|Fri entr[eé])\)\s*", " ", text, flags=re.I).strip(" .")
    if ". " in text:
        title, venue = text.split(". ", 1)
    else:
        title, venue = text, ""
    return title.strip(" ."), venue.strip(" ."), free


def parse_visitorebro_editorial_html(html_text: str, source_url: str, fallback_year: int | None = None):
    soup = BeautifulSoup(html_text or "", "html.parser")
    visible = soup.get_text("\n", strip=True)
    year = _visitorebro_year(visible, fallback=fallback_year)
    events = []
    seen = set()
    for raw in visible.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        parsed = _parse_visitorebro_date_prefix(line, year)
        if not parsed:
            continue
        start_date, end_date, rest = parsed
        title, venue, is_free = _split_visitorebro_title_venue(rest)
        if len(title) < 3 or len(title) > 220:
            continue
        key = (title.casefold(), start_date, venue.casefold())
        if key in seen:
            continue
        seen.add(key)
        external_id = f"{source_url}|{start_date}|{title}|{venue}"
        digest = hashlib.sha1(external_id.encode("utf-8")).hexdigest()[:20]
        events.append(Event(
            id=f"visitorebro-{digest}", title=title,
            event_type=_guess_type(title, ""), category="Okategoriserat",
            start_date=start_date, end_date=end_date, start_time=None,
            venue=venue or "Örebro", city="Örebro", region="Örebro län", country="Sverige",
            official_url=source_url, status="confirmed",
            source_names=["Visit Örebro"], source_count=1,
            source_records=[SourceRecord(source="Visit Örebro", external_id=external_id, source_url=source_url, fetched_at=_now(), raw_title=title)],
            verified_at=_now(), created_at=_now(), updated_at=_now(),
            description="", tags=[], is_demo=False,
            data_quality="partial",
            quality_notes=["Datum, titel och plats importerade från Visit Örebros officiella redaktionella eventlista", "Underliggande arrangörssida har inte korsverifierats i denna import"],
            price_min=0.0 if is_free else None,
            price_max=0.0 if is_free else None,
            currency="SEK", price_status="free" if is_free else "unknown",
        ))
    return _unique(events)


def visitorebro_editorial_events():
    events = []
    for url in VISITOREBRO_EDITORIAL_URLS:
        soup = _get(url)
        events.extend(parse_visitorebro_editorial_html(str(soup), source_url=url))
    return _unique(events)


def _parse_swedish_day_month(text: str, *, year: int | None = None):
    clean = re.sub(r"\s+", " ", (text or "").lower()).replace(".", "")
    m = re.search(r"\b(\d{1,2})\s+(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\b", clean)
    if not m:
        return None
    y = year or date.today().year
    try:
        candidate = date(y, SV_MONTHS[m.group(2)], int(m.group(1)))
    except ValueError:
        return None
    if year is None and candidate < date.today().replace(day=1):
        candidate = date(y + 1, candidate.month, candidate.day)
    return candidate.isoformat()

def _explicit_price(text: str):
    clean = re.sub(r"\s+", " ", (text or "").lower())
    if re.search(r"\b(fri entré|gratis|kostnadsfria biljetter|kostnadsfritt)\b", clean):
        return None, None, "free"
    m = re.search(r"\b(\d{1,5})\s*(?:-|–|—)\s*(\d{1,5})\s*kronor\b", clean)
    if m:
        return float(m.group(1)), float(m.group(2)), "known"
    m = re.search(r"\b(\d{1,5})\s*kronor\b", clean)
    if m:
        v=float(m.group(1))
        return v, v, "known"
    return None, None, "unknown"

def parse_orebro_konserthus_event_page(html_text: str, page_url: str, *, today: date | None = None):
    soup=BeautifulSoup(html_text or "", "html.parser")
    title_node=soup.find("h1")
    title=re.sub(r"\s+"," ",title_node.get_text(" ",strip=True) if title_node else "").strip()
    if not title:
        return None
    text=re.sub(r"\s+"," ",soup.get_text(" ",strip=True))
    year_match=re.search(r"\b(20\d{2})\b", text)
    start_date=_parse_swedish_day_month(text, year=int(year_match.group(1)) if year_match else None)
    if not start_date:
        return None
    tm=re.search(r"\bkl\.?\s*(\d{1,2})[:.](\d{2})\b", text.lower())
    start_time=f"{int(tm.group(1)):02d}:{tm.group(2)}" if tm else None
    pmin,pmax,pstatus=_explicit_price(text)
    venue="Örebro Konserthus"
    for candidate in ["Konsertsalen","Stadsparken"]:
        if candidate.lower() in text.lower():
            venue=candidate if candidate=="Stadsparken" else "Örebro Konserthus"
            break
    digest=hashlib.sha1(page_url.encode("utf-8")).hexdigest()[:20]
    return Event(
        id=f"orebro-kh-{digest}",title=title,event_type="Konsert",category="Musik",
        start_date=start_date,end_date=None,start_time=start_time,venue=venue,city="Örebro",region="Örebro län",country="Sverige",
        official_url=page_url,status="confirmed",source_names=["Örebro Konserthus"],source_count=1,
        source_records=[SourceRecord(source="Örebro Konserthus",external_id=page_url,source_url=page_url,fetched_at=_now(),raw_title=title)],
        verified_at=_now(),created_at=_now(),updated_at=_now(),description="",tags=["Musik"],is_demo=False,
        data_quality="source_verified",quality_notes=["Titel, datum och metadata hämtade från officiell eventsida"],
        price_min=pmin,price_max=pmax,currency="SEK",price_status=pstatus
    )

def parse_orebro_teater_calendar_html(html_text: str, *, today: date | None = None):
    soup=BeautifulSoup(html_text or "", "html.parser")
    source=source_by_key("orebro_teater")
    events=[]
    seen=set()
    current_date=None
    # Calendar headings carry dates; following links until next date heading belong to that date.
    for node in soup.find_all(["h2","h3","h4","a"]):
        if node.name in {"h2","h3","h4"}:
            raw=node.get_text(" ",strip=True)
            m=re.search(r"\b(\d{1,2})\s+(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\s+(20\d{2})\b", raw.lower())
            if m:
                try: current_date=date(int(m.group(3)),SV_MONTHS[m.group(2)],int(m.group(1))).isoformat()
                except ValueError: current_date=None
            continue
        if not current_date:
            continue
        href=(node.get("href") or "").strip()
        title_node = node.select_one(".event-title")
        # The production link also wraps an excerpt on the live site. Prefer its
        # explicit title metadata so descriptive copy never becomes part of identity.
        title = (node.get("title") or (title_node.get_text(" ", strip=True) if title_node else "") or node.get_text(" ", strip=True))
        title=re.sub(r"\s+"," ",title).strip()
        if not href or not title or title.lower() in {"köp biljett","läs mer"}:
            continue
        absolute=urljoin(source.url,href)
        if ("/forestallning" not in absolute.casefold()
                or absolute.split("?", 1)[0].rstrip("/") == source.url.split("?", 1)[0].rstrip("/")):
            continue
        event_key = f"{absolute}|{current_date}"
        if event_key in seen or "orebroteater.se" not in absolute:
            continue
        # Only event/production-like links with meaningful text.
        if len(title)<3 or len(title)>180:
            continue
        seen.add(event_key)
        digest=hashlib.sha1(event_key.encode("utf-8")).hexdigest()[:20]
        events.append(Event(
            id=f"orebro-teater-{digest}",title=title,event_type="Teater",category="Scen & teater",
            start_date=current_date,end_date=None,start_time=None,venue="Örebro Teater",city="Örebro",region="Örebro län",country="Sverige",
            official_url=absolute,status="confirmed",source_names=["Örebro Teater"],source_count=1,
            source_records=[SourceRecord(source="Örebro Teater",external_id=f"{absolute}|{current_date}",source_url=absolute,fetched_at=_now(),raw_title=title)],
            verified_at=_now(),created_at=_now(),updated_at=_now(),description="",tags=["Teater"],is_demo=False,
            data_quality="partial",quality_notes=["Datum och titel importerade från Örebro Teaters officiella kalendarium"]
        ))
    return _unique(events)

def orebro_konserthus_events():
    source=source_by_key("orebro_konserthus")
    soup=_get(source.url)
    links=[]
    for a in soup.find_all("a",href=True):
        u=urljoin(source.url,a.get("href"))
        if "/evenemang/" in u and u.rstrip("/") != source.url.rstrip("/") and u not in links:
            links.append(u)
    rows=[]
    for url in links[:40]:
        try:
            detail=_get(url)
            e=parse_orebro_konserthus_event_page(str(detail),url)
            if e and date.fromisoformat(e.start_date) >= date.today():
                rows.append(e)
        except Exception:
            continue
    from booking_enrichment import enrich_events
    return enrich_events(_unique(rows),max_fetches=12,workers=6,timeout=10)

def orebro_teater_events():
    source=source_by_key("orebro_teater")
    soup=_get(source.url)
    return parse_orebro_teater_calendar_html(str(soup))
