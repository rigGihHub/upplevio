from datetime import datetime, timezone
import re
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
        id=f"{source_key}-{abs(hash(external_id))}",
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
