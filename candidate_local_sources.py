from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from booking_enrichment import enrich_events
from booking_intent import cta_quality
from dedupe import deduplicate
from models import Event, SourceRecord
from coverage_frontier import classify_frontier, coverage_frontier

CANDIDATES = {
    "kulturkvarteret": {
        "name": "Kulturkvarteret",
        "url": "https://kulturkvarteret.orebro.se/kulturkvarteret/evenemang.4.670655db1749fdf9704308.html",
        "venue": "Kulturkvarteret",
    },
    "wadkoping": {
        "name": "Wadköping",
        "url": "https://guide.orebro.se/wadkoping/evenemang.4.7bb58d5d154d257e2bc113ac.html",
        "venue": "Wadköping",
    },
    "orebro_county_museum": {
        "name": "Örebro läns museum",
        "url": "https://olm.se/kalender/",
        "venue": "Örebro läns museum",
    },
    "orebro_university": {
        "name": "Örebro universitet",
        "url": "https://www.oru.se/kalendarium/",
        "venue": "Örebro universitet",
        "urls": [
            "https://www.oru.se/kalendarium/",
            "https://www.oru.se/kalendarium/oppna-forelasningar/",
            "https://www.oru.se/kalendarium/ovriga-evenemang/",
        ],
    },
    "orebro_church": {
        "name": "Svenska kyrkan i Örebro",
        "url": "https://www.svenskakyrkan.se/orebro/kalender",
        "venue": "",
    },
    "karlslund": {
        "name": "Karlslund",
        "url": "https://extra.orebro.se/karlslund",
        "venue": "Karlslunds herrgård med trädgård",
    },
    "makeriet": {
        "name": "Makeriet i Örebro",
        "url": "https://makerietorebro.se/",
        "venue": "Makeriet i Örebro",
    },
}

MONTHS = {
    "januari":1,"februari":2,"mars":3,"april":4,"maj":5,"juni":6,
    "juli":7,"augusti":8,"september":9,"oktober":10,"november":11,"december":12,
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _get(url, timeout=20):
    r=requests.get(url,timeout=timeout,headers={"User-Agent":"Upplevio/0.46 (+candidate source audit)"})
    r.raise_for_status()
    return r.text


def _date_piece(day, month, year):
    try:
        return date(year, MONTHS[month], int(day))
    except (ValueError, KeyError):
        return None


def parse_swedish_candidate_range(text, *, today=None):
    """Parse official calendar forms without inventing a date.

    Supports e.g. '10 september', '12 maj–15 augusti', '28–29 september'.
    Missing year is interpreted as the next plausible occurrence.
    """
    today=today or date.today()
    clean=re.sub(r"\s+"," ",(text or "").lower().replace("—","–").replace("-","–")).strip()
    year_match=re.search(r"\b(20\d{2})\b",clean)
    year=int(year_match.group(1)) if year_match else today.year

    m=re.search(r"\b(\d{1,2})\s+(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\s*–\s*(\d{1,2})\s+(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\b",clean)
    if m:
        start=_date_piece(m.group(1),m.group(2),year)
        end=_date_piece(m.group(3),m.group(4),year)
    else:
        m=re.search(r"\b(\d{1,2})\s*–\s*(\d{1,2})\s+(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\b",clean)
        if m:
            start=_date_piece(m.group(1),m.group(3),year)
            end=_date_piece(m.group(2),m.group(3),year)
        else:
            m=re.search(r"\b(\d{1,2})\s+(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\b",clean)
            if not m:
                return None,None
            start=_date_piece(m.group(1),m.group(2),year)
            end=start
    if not start or not end:
        return None,None
    if not year_match and end < today.replace(day=1):
        try:
            start=start.replace(year=start.year+1)
            end=end.replace(year=end.year+1)
        except ValueError:
            return None,None
    if end < start:
        try:
            end=end.replace(year=end.year+1)
        except ValueError:
            return None,None
    return start.isoformat(),end.isoformat()


def _guess_type(prefix, title):
    text=f"{prefix} {title}".lower()
    if "konsert" in text or "musik" in text:
        return "Konsert"
    if any(x in text for x in ["scenkonst","teater","dans"]):
        return "Teater" if "teater" in text else "Scenkonst"
    if any(x in text for x in ["för barn","familj"]):
        return "Familj"
    if any(x in text for x in ["utställning","konst"]):
        return "Utställning"
    if any(x in text for x in ["föreläsning","samtal"]):
        return "Föreläsning"
    if any(x in text for x in ["marknad","mässa"]):
        return "Marknad"
    if any(x in text for x in ["delta själv","workshop","prova på"]):
        return "Aktivitet"
    return "Evenemang"


def parse_candidate_calendar(html_text, *, key, today=None):
    cfg=CANDIDATES[key]
    soup=BeautifulSoup(html_text or "","html.parser")
    events=[]
    seen=set()
    # Official SiteVision calendars expose event cards around links/headings.
    for node in soup.find_all(["h2","h3","h4","a"]):
        title=re.sub(r"\s+"," ",node.get_text(" ",strip=True)).strip()
        if not title or len(title)<3 or len(title)>180:
            continue
        low=title.casefold()
        if low in {"läs mer","visa mer","till evenemangskalendern","rensa alla filter","evenemang"}:
            continue
        container=node.find_parent(["article","li"]) or node.find_parent("div") or node.parent
        text=re.sub(r"\s+"," ",container.get_text(" ",strip=True) if container else title).strip()
        start,end=parse_swedish_candidate_range(text,today=today)
        if not start:
            continue
        href=(node.get("href") if node.name=="a" else None)
        if not href and container:
            a=container.find("a",href=True)
            href=a.get("href") if a else None
        url=urljoin(cfg["url"],href) if href else cfg["url"]
        identity=(title.casefold(),start,url)
        if identity in seen:
            continue
        seen.add(identity)
        # Prefix is typically the short category text before the title in SiteVision cards.
        prefix=text[: max(0,text.find(title))] if title in text else ""
        event_type=_guess_type(prefix,title)
        eid=hashlib.sha1(f"{key}|{title}|{start}|{url}".encode("utf-8")).hexdigest()[:20]
        events.append(Event(
            id=f"candidate-{key}-{eid}",title=title,event_type=event_type,category=event_type,
            start_date=start,end_date=end if end!=start else None,start_time=None,
            venue=cfg["venue"],city="Örebro",region="Örebro län",country="Sverige",
            official_url=url,status="confirmed",source_names=[cfg["name"]],source_count=1,
            source_records=[SourceRecord(source=cfg["name"],external_id=eid,source_url=url,fetched_at=_now(),raw_title=title)],
            verified_at=_now(),created_at=_now(),updated_at=_now(),description="",tags=[],is_demo=False,
            data_quality="partial",quality_notes=["Kandidatimport – påverkar inte publik discovery"]
        ))
    return events



def _oru_title_and_date(text):
    clean=re.sub(r"\s+"," ",(text or "")).strip()
    m=re.search(
        r"\b(\d{1,2})\s+(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\s+(20\d{2})\b",
        clean, re.I
    )
    if not m:
        return None,None,None
    title=clean[:m.start()].strip(" ·–—-")
    if not title or len(title)>180:
        return None,None,None
    try:
        d=date(int(m.group(3)),MONTHS[m.group(2).lower()],int(m.group(1)))
    except Exception:
        return None,None,None
    tail=clean[m.end():].strip()
    return title,d.isoformat(),tail


def parse_orebro_university_public_calendar(html_text, *, page_url=None):
    """Strict candidate parser for publicly accessible, locally relevant ORU events.

    We deliberately require an explicit 'Öppet för alla' marker and local Örebro evidence.
    This under-imports rather than leaking internal/student-only calendar items into discovery.
    """
    cfg=CANDIDATES["orebro_university"]
    soup=BeautifulSoup(html_text or "","html.parser")
    events=[]
    seen=set()
    for a in soup.find_all("a",href=True):
        text=re.sub(r"\s+"," ",a.get_text(" ",strip=True)).strip()
        low=text.casefold()
        if "öppet för alla" not in low:
            continue
        if any(x in low for x in ["endast öppna för studenter", "endast öppet för studenter", "endast för studenter", "endast för anställda"]):
            continue
        # Candidate is specifically for Örebro-area coverage; avoid remote/other-campus inflation.
        if "örebro" not in low:
            continue
        if any(x in low for x in ["stockholm", "campus grythyttan", "digitalt seminarium", "digitalt evenemang"]):
            continue
        title,start,tail=_oru_title_and_date(text)
        if not start:
            continue
        tm=re.search(r"\b([01]?\d|2[0-3]):[0-5]\d\b",tail)
        start_time=tm.group(0).zfill(5) if tm else None
        href=urljoin(page_url or cfg["url"],a.get("href"))
        identity=(title.casefold(),start,start_time or "",href)
        if identity in seen:
            continue
        seen.add(identity)
        event_type=_guess_type("Öppet för alla",title)
        eid=hashlib.sha1(f"orebro_university|{title}|{start}|{href}".encode("utf-8")).hexdigest()[:20]
        events.append(Event(
            id=f"candidate-orebro_university-{eid}",title=title,event_type=event_type,category=event_type,
            start_date=start,end_date=None,start_time=start_time,
            venue=cfg["venue"],city="Örebro",region="Örebro län",country="Sverige",
            official_url=href,status="confirmed",source_names=[cfg["name"]],source_count=1,
            source_records=[SourceRecord(source=cfg["name"],external_id=eid,source_url=href,fetched_at=_now(),raw_title=title)],
            verified_at=_now(),created_at=_now(),updated_at=_now(),description="",tags=["öppet för alla"],is_demo=False,
            data_quality="partial",quality_notes=["Kandidatimport – endast poster uttryckligen märkta Öppet för alla", "Påverkar inte publik discovery"]
        ))
    return events



def parse_orebro_county_museum_calendar(html_text, *, page_url=None, today=None):
    """Conservative parser for Örebro läns museum's official calendar.

    Only calendar-like links/cards with an explicit Swedish date are accepted.
    Location is not invented: events outside Örebro city remain region-level candidates
    and can later be filtered by the normal geography layer.
    """
    cfg=CANDIDATES["orebro_county_museum"]
    soup=BeautifulSoup(html_text or "","html.parser")
    events=[]
    seen=set()
    for a in soup.find_all("a",href=True):
        title=re.sub(r"\s+"," ",a.get_text(" ",strip=True)).strip()
        if not title or len(title)<3 or len(title)>180 or title.casefold() in {"läs mer","se hela kalendern","kalender"}:
            continue
        container=a.find_parent(["article","li"]) or a.find_parent("div") or a.parent
        text=re.sub(r"\s+"," ",(container.get_text(" ",strip=True) if container else title)).strip()
        start,end=parse_swedish_candidate_range(text,today=today)
        if not start:
            continue
        # Reject obvious navigation/search links; require calendar detail semantics or date close to title.
        href=urljoin(page_url or cfg["url"],a.get("href"))
        if any(x in href.casefold() for x in ["/tag/","/sok","?query="]):
            continue
        prefix=text[:max(0,text.find(title))] if title in text else ""
        suffix=text[text.find(title)+len(title):] if title in text else text
        event_type=_guess_type(f"{prefix} {suffix}",title)
        tags=[]
        low=text.casefold()
        for tag in ["barn","föreläsning","hantverk","utställning","visning","arkeologi","bebyggelse","mobila museet"]:
            if tag in low:
                tags.append(tag)
        eid=hashlib.sha1(f"orebro_county_museum|{title}|{start}|{href}".encode("utf-8")).hexdigest()[:20]
        identity=(title.casefold(),start,href)
        if identity in seen:
            continue
        seen.add(identity)
        events.append(Event(
            id=f"candidate-orebro_county_museum-{eid}",title=title,event_type=event_type,category=event_type,
            start_date=start,end_date=end if end!=start else None,start_time=None,
            venue=cfg["venue"],city="",region="Örebro län",country="Sverige",official_url=href,status="confirmed",
            source_names=[cfg["name"]],source_count=1,
            source_records=[SourceRecord(source=cfg["name"],external_id=eid,source_url=href,fetched_at=_now(),raw_title=title)],
            verified_at=_now(),created_at=_now(),updated_at=_now(),description="",tags=tags,is_demo=False,
            data_quality="partial",quality_notes=["Kandidatimport – officiell kalender", "Ort lämnas tom när kalenderkortet inte uttryckligen verifierar Örebro stad", "Påverkar inte publik discovery"]
        ))
    return events


def orebro_county_museum_candidate_events(*, timeout=20, enrich_booking=True):
    cfg=CANDIDATES["orebro_county_museum"]
    html=_get(cfg["url"],timeout=timeout)
    rows=parse_orebro_county_museum_calendar(html,page_url=cfg["url"])
    if enrich_booking:
        rows=enrich_events(rows,max_fetches=8,workers=4,timeout=8)
    return rows


def orebro_university_candidate_events(*, timeout=20, enrich_booking=True):
    cfg=CANDIDATES["orebro_university"]
    rows=[]
    for url in cfg.get("urls") or [cfg["url"]]:
        html=_get(url,timeout=timeout)
        rows.extend(parse_orebro_university_public_calendar(html,page_url=url))
    # exact duplicate collapse across ORU category pages
    unique={}
    for e in rows:
        unique[(e.title.casefold(),e.start_date,e.start_time or "",e.official_url or "")]=e
    rows=list(unique.values())
    if enrich_booking:
        rows=enrich_events(rows,max_fetches=8,workers=4,timeout=8)
    return rows


def _church_numeric_date(text, *, today=None):
    today=today or date.today()
    clean=re.sub(r"\s+"," ",(text or "")).strip()
    m=re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(20\d{2}|\d{2}))?\b",clean)
    if not m:
        return None
    day,month=int(m.group(1)),int(m.group(2))
    year=today.year
    if m.group(3):
        raw=m.group(3)
        year=int(raw) if len(raw)==4 else 2000+int(raw)
    try:
        d=date(year,month,day)
    except ValueError:
        return None
    if not m.group(3) and d < today.replace(day=1):
        try:
            d=d.replace(year=d.year+1)
        except ValueError:
            return None
    return d.isoformat()


def parse_orebro_church_public_calendar(html_text, *, page_url=None, today=None):
    """Strict candidate parser for public discovery-worthy items in Svenska kyrkan i Örebro.

    The source contains many recurring services and internal/group activities. Upplevio only
    accepts cards with an explicit date plus strong cultural/community discovery markers.
    Ordinary worship, prayer, rehearsals and closed/member-only activities are excluded.
    """
    cfg=CANDIDATES["orebro_church"]
    today=today or date.today()
    soup=BeautifulSoup(html_text or "","html.parser")
    events=[]
    seen=set()
    include=("konsert","föreläs","författar","vernissage","visning","guidning","samtal","föredrag","marknad","festival","utställning","retreat","kultur","musikprogram")
    exclude=("gudstjänst","högmässa","mässa ","morgonbön","bönegrupp","bibelstudium","körövning","repetition","endast för","medlemsmöte")
    for node in soup.find_all(["article","li","h2","h3","h4","a"]):
        text=re.sub(r"\s+"," ",node.get_text(" ",strip=True)).strip()
        if not text or len(text)<8:
            continue
        low=text.casefold()
        if not any(k in low for k in include) or any(k in low for k in exclude):
            continue
        start,end=parse_swedish_candidate_range(text,today=today)
        if not start:
            start=_church_numeric_date(text,today=today)
            end=start
        if not start:
            continue
        title=""
        if node.name in {"h2","h3","h4","a"}:
            title=re.sub(r"\s+"," ",node.get_text(" ",strip=True)).strip()
        else:
            h=node.find(["h2","h3","h4"])
            a=node.find("a",href=True)
            title=re.sub(r"\s+"," ",(h or a).get_text(" ",strip=True)).strip() if (h or a) else ""
        if not title or len(title)>180:
            title=re.split(r"\b(?:\d{1,2}\s+(?:januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)|\d{1,2}/\d{1,2})\b",text,maxsplit=1,flags=re.I)[0].strip(" ·–—-")
        if len(title)<3 or len(title)>180:
            continue
        a=node if node.name=="a" and node.get("href") else node.find("a",href=True)
        href=urljoin(page_url or cfg["url"],a.get("href")) if a else (page_url or cfg["url"])
        identity=(title.casefold(),start,href)
        if identity in seen:
            continue
        seen.add(identity)
        event_type=_guess_type(text,title)
        tags=["community","förening"]
        for tag in ["konsert","föreläsning","vernissage","visning","samtal","föredrag","marknad","festival","utställning","retreat"]:
            if tag in low:
                tags.append(tag)
        is_free=bool(re.search(r"\b(?:gratis|ingen kostnad|fri entré)\b",low))
        tm=re.search(r"\b(?:kl\.?\s*)?([01]?\d|2[0-3])[:.]([0-5]\d)\b",text,re.I)
        start_time=f"{int(tm.group(1)):02d}:{tm.group(2)}" if tm else None
        eid=hashlib.sha1(f"orebro_church|{title}|{start}|{href}".encode("utf-8")).hexdigest()[:20]
        events.append(Event(
            id=f"candidate-orebro_church-{eid}",title=title,event_type=event_type,category=event_type,
            start_date=start,end_date=end if end and end!=start else None,start_time=start_time,
            venue="",city="Örebro",region="Örebro län",country="Sverige",official_url=href,status="confirmed",
            source_names=[cfg["name"]],source_count=1,
            source_records=[SourceRecord(source=cfg["name"],external_id=eid,source_url=href,fetched_at=_now(),raw_title=title)],
            verified_at=_now(),created_at=_now(),updated_at=_now(),description="",tags=tags,is_demo=False,
            data_quality="partial",quality_notes=["Kandidatimport – endast tydligt publik kultur/community", "Gudstjänster, bön och interna/återkommande grupper filtreras bort", "Påverkar inte publik discovery"],
            price_status="free" if is_free else "unknown"
        ))
    return events


def orebro_church_candidate_events(*, timeout=20, enrich_booking=True):
    cfg=CANDIDATES["orebro_church"]
    html=_get(cfg["url"],timeout=timeout)
    rows=parse_orebro_church_public_calendar(html,page_url=cfg["url"])
    if enrich_booking:
        rows=enrich_events(rows,max_fetches=8,workers=4,timeout=8)
    return rows



def _explicit_time_range(text: str):
    """Return (start, end) only when the source explicitly contains a clock range."""
    m=re.search(r"\b(?:kl\.?\s*)?([01]?\d|2[0-3])(?:[:.]([0-5]\d))?\s*(?:-|–|—|till)\s*([01]?\d|2[0-3])(?:[:.]([0-5]\d))?\b", text or "", re.I)
    if not m:
        return None, None
    start=f"{int(m.group(1)):02d}:{m.group(2) or '00'}"
    end=f"{int(m.group(3)):02d}:{m.group(4) or '00'}"
    return start,end


def parse_karlslund_public_calendar(html_text, *, page_url=None, today=None):
    """Conservative parser for Karlslund's official municipal event content.

    Only event-like blocks with an explicit calendar date are accepted. General
    destination/opening-hours content is deliberately ignored. Nature/outdoor tags
    are added only when the source text itself supports them.
    """
    cfg=CANDIDATES["karlslund"]
    today=today or date.today()
    soup=BeautifulSoup(html_text or "","html.parser")
    events=[]
    seen=set()
    months="januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december"
    for heading in soup.find_all(["h2","h3","h4"]):
        title=re.sub(r"\s+"," ",heading.get_text(" ",strip=True)).strip()
        if len(title)<3 or len(title)>180:
            continue
        low_title=title.casefold()
        if low_title in {"aktuellt","besöksupplevelser","program & evenemang","öppettider & besöksinformation"}:
            continue
        container=heading.find_parent(["article","li","section"]) or heading.find_parent("div") or heading.parent
        text=re.sub(r"\s+"," ",container.get_text(" ",strip=True) if container else title).strip()
        low=text.casefold()
        m=re.search(rf"\b(\d{{1,2}})\s+({months})(?:\s+(20\d{{2}}))?\b",low,re.I)
        if not m:
            continue
        if any(x in low_title for x in ["öppettider","kontakt","tillgänglighet","historia"]):
            continue
        year=int(m.group(3)) if m.group(3) else today.year
        try:
            d=date(year,MONTHS[m.group(2).lower()],int(m.group(1)))
        except (ValueError,KeyError):
            continue
        if not m.group(3) and d < today.replace(day=1):
            try:
                d=d.replace(year=d.year+1)
            except ValueError:
                continue
        if d < today:
            continue
        a=heading.find("a",href=True) or (container.find("a",href=True) if container else None)
        href=urljoin(page_url or cfg["url"],a.get("href")) if a else (page_url or cfg["url"])
        identity=(title.casefold(),d.isoformat(),href)
        if identity in seen:
            continue
        seen.add(identity)
        range_start, end_time=_explicit_time_range(text)
        tm=re.search(r"\b(?:kl\.?\s*)?([01]?\d|2[0-3])[:.]([0-5]\d)\b",text,re.I)
        start_time=range_start or (f"{int(tm.group(1)):02d}:{tm.group(2)}" if tm else None)
        tags=["Karlslund"]
        for marker,tag in [
            ("marknad","marknad"),("trädgård","natur"),("natur","natur"),
            ("park","outdoor"),("vandring","vandring"),("skörd","outdoor"),
            ("hantverk","hantverk"),("musik","musik"),("barn","familj")
        ]:
            if marker in low and tag not in tags:
                tags.append(tag)
        event_type=_guess_type(text,title)
        is_free=bool(re.search(r"\b(?:gratis|fri entré|ingen kostnad)\b",low))
        eid=hashlib.sha1(f"karlslund|{title}|{d.isoformat()}|{href}".encode("utf-8")).hexdigest()[:20]
        events.append(Event(
            id=f"candidate-karlslund-{eid}",title=title,event_type=event_type,category=event_type,
            start_date=d.isoformat(),end_date=None,start_time=start_time,end_time=end_time,
            venue=cfg["venue"],city="Örebro",region="Örebro län",country="Sverige",official_url=href,status="confirmed",
            source_names=[cfg["name"]],source_count=1,
            source_records=[SourceRecord(source=cfg["name"],external_id=eid,source_url=href,fetched_at=_now(),raw_title=title)],
            verified_at=_now(),created_at=_now(),updated_at=_now(),description="",tags=tags,is_demo=False,
            data_quality="partial",quality_notes=["Kandidatimport – officiell kommunal Karlslund-källa", "Endast poster med explicit datum", "Påverkar inte publik discovery"],
            price_status="free" if is_free else "unknown"
        ))
    return events


def karlslund_candidate_events(*, timeout=20, enrich_booking=True):
    cfg=CANDIDATES["karlslund"]
    html=_get(cfg["url"],timeout=timeout)
    rows=parse_karlslund_public_calendar(html,page_url=cfg["url"])
    if enrich_booking:
        rows=enrich_events(rows,max_fetches=8,workers=4,timeout=8)
    return rows



def parse_makeriet_nightlife_calendar(html_text, *, page_url=None, today=None):
    """Strict nightlife candidate parser for Makeriet's official event calendar.

    Only dated event cards with strong entertainment/nightlife signals are accepted.
    Food/drink promotions and ordinary opening-hours content are explicitly ignored.
    """
    cfg=CANDIDATES["makeriet"]
    today=today or date.today()
    soup=BeautifulSoup(html_text or "","html.parser")
    events=[]
    seen=set()
    include=("stand-up","standup","comedy","klubb","club","dj","konsert","live","pubkör","karaoke","quiz","dans","show","teater","festival")
    exclude=("musselfrossa","aperitif","after work","lunch","middag","brunch","cocktail","öppettid")
    months="januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december|jan|feb|mar|apr|maj|jun|jul|aug|sep|okt|nov|dec"
    month_map={**MONTHS,"jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"aug":8,"sep":9,"okt":10,"nov":11,"dec":12}
    for heading in soup.find_all(["h2","h3","h4"]):
        title=re.sub(r"\s+"," ",heading.get_text(" ",strip=True)).strip()
        if len(title)<3 or len(title)>180:
            continue
        low_title=title.casefold()
        if not any(k in low_title for k in include) or any(k in low_title for k in exclude):
            continue
        container=heading.find_parent(["article","li","section"]) or heading.find_parent("div") or heading.parent
        text=re.sub(r"\s+"," ",container.get_text(" ",strip=True) if container else title).strip()
        low=text.casefold()
        if any(k in low for k in exclude):
            continue
        m=re.search(rf"\b(\d{{1,2}})\s+({months})(?:\s+(20\d{{2}}))?\b",low,re.I)
        if not m:
            # WordPress event detail pages often expose YYYY-MM-DD.
            iso=re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b",text)
            if not iso:
                continue
            try:
                d=date(int(iso.group(1)),int(iso.group(2)),int(iso.group(3)))
            except ValueError:
                continue
        else:
            raw_month=m.group(2).lower()
            year=int(m.group(3)) if m.group(3) else today.year
            try:
                d=date(year,month_map[raw_month],int(m.group(1)))
            except (ValueError,KeyError):
                continue
            if not m.group(3) and d < today.replace(day=1):
                try: d=d.replace(year=d.year+1)
                except ValueError: continue
        if d < today:
            continue
        a=heading.find("a",href=True) or (container.find("a",href=True) if container else None)
        href=urljoin(page_url or cfg["url"],a.get("href")) if a else (page_url or cfg["url"])
        identity=(title.casefold(),d.isoformat(),href)
        if identity in seen:
            continue
        seen.add(identity)
        range_start, end_time=_explicit_time_range(text)
        tm=re.search(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b",text)
        start_time=range_start or (f"{int(tm.group(1)):02d}:{tm.group(2)}" if tm else None)
        tags=["nightlife"]
        for marker,tag in [("comedy","comedy"),("stand-up","comedy"),("standup","comedy"),("klubb","club"),("club","club"),("dj","dj"),("konsert","musik"),("live","musik"),("pubkör","musik"),("karaoke","karaoke"),("quiz","quiz"),("dans","dans")]:
            if marker in low and tag not in tags:
                tags.append(tag)
        event_type="Comedy" if "comedy" in tags else ("Konsert" if "musik" in tags else ("Klubb" if "club" in tags or "dj" in tags else "Evenemang"))
        is_free=bool(re.search(r"\b(?:gratis|fri entré|ingen kostnad)\b",low))
        eid=hashlib.sha1(f"makeriet|{title}|{d.isoformat()}|{href}".encode("utf-8")).hexdigest()[:20]
        events.append(Event(
            id=f"candidate-makeriet-{eid}",title=title,event_type=event_type,category=event_type,
            start_date=d.isoformat(),end_date=None,start_time=start_time,end_time=end_time,
            venue=cfg["venue"],city="Örebro",region="Örebro län",country="Sverige",official_url=href,status="confirmed",
            source_names=[cfg["name"]],source_count=1,
            source_records=[SourceRecord(source=cfg["name"],external_id=eid,source_url=href,fetched_at=_now(),raw_title=title)],
            verified_at=_now(),created_at=_now(),updated_at=_now(),description="",tags=tags,is_demo=False,
            data_quality="partial",quality_notes=["Kandidatimport – officiell venuekalender", "Mat-/dryckespromotions och öppettider filtreras bort", "Påverkar inte publik discovery"],
            price_status="free" if is_free else "unknown"
        ))
    return events


def makeriet_candidate_events(*, timeout=20, enrich_booking=True):
    cfg=CANDIDATES["makeriet"]
    html=_get(cfg["url"],timeout=timeout)
    rows=parse_makeriet_nightlife_calendar(html,page_url=cfg["url"])
    if enrich_booking:
        rows=enrich_events(rows,max_fetches=8,workers=4,timeout=8)
    return rows

def candidate_source_events(key, *, timeout=20, enrich_booking=True):
    if key == "orebro_county_museum":
        return orebro_county_museum_candidate_events(timeout=timeout,enrich_booking=enrich_booking)
    if key == "orebro_university":
        return orebro_university_candidate_events(timeout=timeout,enrich_booking=enrich_booking)
    if key == "orebro_church":
        return orebro_church_candidate_events(timeout=timeout,enrich_booking=enrich_booking)
    if key == "karlslund":
        return karlslund_candidate_events(timeout=timeout,enrich_booking=enrich_booking)
    if key == "makeriet":
        return makeriet_candidate_events(timeout=timeout,enrich_booking=enrich_booking)
    html=_get(CANDIDATES[key]["url"],timeout=timeout)
    rows=parse_candidate_calendar(html,key=key)
    if enrich_booking:
        # Only candidate detail pages, capped to protect latency.
        rows=enrich_events(rows,max_fetches=8,workers=4,timeout=8)
    return rows


def fetch_candidate_sources(keys=("kulturkvarteret","wadkoping","orebro_university","orebro_county_museum","orebro_church","karlslund","makeriet")):
    rows=[]
    health=[]
    for key in keys:
        cfg=CANDIDATES[key]
        try:
            source_rows=candidate_source_events(key)
            rows.extend(source_rows)
            health.append({"source":cfg["name"],"status":"OK","events":len(source_rows),"error":None})
        except Exception as exc:
            health.append({"source":cfg["name"],"status":"Fel","events":0,"error":str(exc)[:180]})
    return rows,health


def candidate_value_audit(existing_events, candidate_events, *, today=None):
    """Simulate enabling candidates without changing public discovery.

    Value is not just "more rows". We also measure whether the source contributes
    unique events inside Coverage Frontier segments that are currently thin or
    absent in the existing import. This remains descriptive evidence, not a score.
    """
    existing_copy=deepcopy(list(existing_events or []))
    candidate_copy=deepcopy(list(candidate_events or []))
    merged,_=deduplicate(existing_copy+candidate_copy)
    candidate_names={cfg["name"] for cfg in CANDIDATES.values()}

    frontier=coverage_frontier(existing_copy, today=today)
    underserved={r["segment"] for r in frontier["rows"] if r["status"] != "Bra täckning"}

    by={name:{
        "candidate_events":0,"unique_events":0,"overlap_events":0,"bookable":0,
        "event_types":set(),"unique_event_types":set(),"frontier_segments":set(),
        "unique_frontier_segments":set(),"underserved_segments":set(),
        "unique_events_in_underserved_segments":0,
    } for name in candidate_names}
    raw_counts={name:0 for name in candidate_names}
    for e in candidate_events:
        for name in set(e.source_names or []):
            if name in raw_counts:
                raw_counts[name]+=1
                by[name]["frontier_segments"].update(classify_frontier(e))

    for e in merged:
        names=set(e.source_names or [])
        candidates=names & candidate_names
        if not candidates:
            continue
        segments=set(classify_frontier(e))
        for name in candidates:
            row=by[name]
            row["candidate_events"]=raw_counts[name]
            row["event_types"].add(e.event_type or "Okänd")
            if names == {name}:
                row["unique_events"]+=1
                row["unique_event_types"].add(e.event_type or "Okänd")
                row["unique_frontier_segments"].update(segments)
                underserved_hits=segments & underserved
                if underserved_hits:
                    row["unique_events_in_underserved_segments"]+=1
                    row["underserved_segments"].update(underserved_hits)
            else:
                row["overlap_events"]+=1
            if cta_quality(e)["status"]=="bookable":
                row["bookable"]+=1

    result=[]
    for name,row in by.items():
        total=row["unique_events"]+row["overlap_events"]
        result.append({
            "source":name,
            "candidate_events":raw_counts[name],
            "represented_after_dedupe":total,
            "unique_events":row["unique_events"],
            "overlap_events":row["overlap_events"],
            "unique_share":row["unique_events"]/total if total else None,
            "bookable":row["bookable"],
            "event_types":sorted(row["event_types"]),
            "unique_event_types":sorted(row["unique_event_types"]),
            "frontier_segments":sorted(row["frontier_segments"]),
            "unique_frontier_segments":sorted(row["unique_frontier_segments"]),
            "underserved_segments":sorted(row["underserved_segments"]),
            "unique_events_in_underserved_segments":row["unique_events_in_underserved_segments"],
        })
    result.sort(key=lambda r:(
        -r["unique_events_in_underserved_segments"],-r["unique_events"],
        -len(r["unique_frontier_segments"]),r["source"].casefold()
    ))
    return result
