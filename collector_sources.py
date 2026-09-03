from datetime import datetime, timezone
import re
import requests
from bs4 import BeautifulSoup
from models import Event, SourceRecord
from taxonomy import classify
import hashlib

def _now():
    return datetime.now(timezone.utc).isoformat()

MONTHS = {
    "januari":1,"februari":2,"mars":3,"april":4,"maj":5,"juni":6,
    "juli":7,"augusti":8,"september":9,"oktober":10,"november":11,"december":12
}

def _range(text):
    clean=re.sub(r"\s+"," ",(text or "").lower()).strip()
    # 5–6 September 2026 / 5-6 september 2026
    m=re.search(r"(\d{1,2})\s*[-–]\s*(\d{1,2})\s+([a-zåäö]+)\s+(20\d{2})",clean)
    if m and m.group(3) in MONTHS:
        d1,d2,mo,y=int(m.group(1)),int(m.group(2)),MONTHS[m.group(3)],int(m.group(4))
        return f"{y:04d}-{mo:02d}-{d1:02d}", f"{y:04d}-{mo:02d}-{d2:02d}"
    m=re.search(r"(\d{1,2})\s+([a-zåäö]+)\s+(20\d{2})",clean)
    if m and m.group(2) in MONTHS:
        d,mo,y=int(m.group(1)),MONTHS[m.group(2)],int(m.group(3))
        iso=f"{y:04d}-{mo:02d}-{d:02d}"
        return iso,iso
    return None,None

def _fetch(url):
    r=requests.get(url,timeout=25,headers={"User-Agent":"Upplevio/0.7 event-discovery prototype"})
    r.raise_for_status()
    return r.url, BeautifulSoup(r.text,"html.parser")

def kortcentralen_events():
    """
    Experimental adapter for Kortcentralen's public event page.
    Kept off by default until verified in the deployed runtime.
    """
    url="https://kortcentralen.se/event-handelser"
    final_url,soup=_fetch(url)
    events=[]
    for heading in soup.find_all(["h2","h3","h4"]):
        title=heading.get_text(" ",strip=True)
        if not title or len(title)>140:
            continue
        container=heading.find_parent(["article","section","li","div"]) or heading.parent
        text=container.get_text(" ",strip=True) if container else ""
        start,end=_range(text)
        if not start:
            continue
        cls=classify(title,text,"Mässa","Samlarkort")
        city=""
        # Known Swedish place names are safer than guessing arbitrary tokens.
        for candidate in ["Göteborg","Kristianstad","Malmö","Mölndal","Norrköping","Skara","Stockholm","Västerås","Örebro"]:
            if candidate.lower() in text.lower():
                city=candidate
                break
        link=heading.find("a") or (container.find("a") if container else None)
        href=link.get("href") if link else None
        if href and href.startswith("/"):
            href="https://kortcentralen.se"+href
        ext=href or f"{title}-{start}"
        events.append(Event(
            id=f"kortcentralen-{hashlib.sha1(str(ext).encode("utf-8")).hexdigest()[:20]}",title=title,event_type=cls.event_type,
            category=cls.category,start_date=start,end_date=end,start_time=None,
            venue="",city=city,region="",country="Sverige",official_url=href,
            status="confirmed",source_names=["Kortcentralen"],source_count=1,
            source_records=[SourceRecord(source="Kortcentralen",external_id=ext,source_url=href or final_url,fetched_at=_now(),raw_title=title)],
            verified_at=_now(),created_at=_now(),updated_at=_now(),description=text,
            tags=cls.tags,is_demo=False,data_quality="partial",
            quality_notes=["Specialiserad samlarkortskalender; live-parser måste bevakas"]
        ))
    # local duplicate safety
    uniq={}
    for e in events:
        uniq[(e.title.lower(),e.start_date,e.city)]=e
    return list(uniq.values())

def tickster_collector_events():
    """
    Experimental search-based adapter. Tickster is valuable for named Swedish
    collector/retro events, but this is not treated as an official API.
    """
    url="https://www.tickster.com/se/sv/events/search?q=samlarkort"
    final_url,soup=_fetch(url)
    events=[]
    text=soup.get_text("\n",strip=True)
    # Conservative line-oriented fallback.
    lines=[re.sub(r"\s+"," ",x).strip() for x in text.splitlines() if x.strip()]
    for i,line in enumerate(lines):
        lower=line.lower()
        if not any(k in lower for k in ["samlarkort","retromania","card summit","pokémonmäss","pokemonmäss"]):
            continue
        context=" ".join(lines[i:i+4])
        start,end=_range(context)
        if not start:
            continue
        cls=classify(line,context,"Mässa","Samlarkort")
        city=""
        for candidate in ["Göteborg","Malmö","Mölndal","Norrköping","Stockholm","Västerås","Örebro","Jönköping"]:
            if candidate.lower() in context.lower():
                city=candidate;break
        ext=f"{line}-{start}-{city}"
        events.append(Event(
            id=f"tickster-collector-{hashlib.sha1(str(ext).encode("utf-8")).hexdigest()[:20]}",title=line,event_type=cls.event_type,
            category=cls.category,start_date=start,end_date=end,start_time=None,
            venue="",city=city,region="",country="Sverige",official_url=final_url,
            ticket_url=final_url,status="confirmed",source_names=["Tickster"],source_count=1,
            source_records=[SourceRecord(source="Tickster",external_id=ext,source_url=final_url,fetched_at=_now(),raw_title=line)],
            verified_at=_now(),created_at=_now(),updated_at=_now(),description=context,
            tags=cls.tags,is_demo=False,data_quality="partial",
            quality_notes=["Sökbaserad Tickster-import; bör senare ersättas av stabilare eventlänkar/API om tillgängligt"]
        ))
    uniq={}
    for e in events:
        uniq[(e.title.lower(),e.start_date,e.city)]=e
    return list(uniq.values())

def experimental_collector_events(enabled_keys):
    mapping={"kortcentralen":kortcentralen_events,"tickster_collectors":tickster_collector_events}
    result=[];health=[]
    for key in enabled_keys or []:
        fn=mapping.get(key)
        if not fn: continue
        name="Kortcentralen" if key=="kortcentralen" else "Tickster – samlare"
        try:
            rows=fn()
            result.extend(rows)
            health.append((name,"OK (experimentell)",len(rows),"Specialiserad samlarkälla"))
        except Exception as exc:
            health.append((name,"Fel",0,str(exc)))
    return result,health
