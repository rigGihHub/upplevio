from datetime import datetime, timezone
import re, requests
from bs4 import BeautifulSoup
from models import Event, SourceRecord
from taxonomy import classify

MONTHS={"jan":1,"feb":2,"mar":3,"apr":4,"maj":5,"jun":6,"jul":7,"aug":8,"sep":9,"okt":10,"nov":11,"dec":12}
def _now(): return datetime.now(timezone.utc).isoformat()
def _date(text):
    text=(text or "").lower().replace(".","")
    m=re.search(r"(\d{1,2})\s+(jan|feb|mar|apr|maj|jun|jul|aug|sep|okt|nov|dec)(?:\s+(20\d{2}))?",text)
    if not m: return None
    year=int(m.group(3) or datetime.now().year)
    return f"{year:04d}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"

def showtic_standup_events():
    url="https://showtic.se/forestallningar/stand-up"
    r=requests.get(url,timeout=25,headers={"User-Agent":"Upplevio/0.7"}); r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser"); out=[]
    for heading in soup.find_all(["h2","h3","h4"]):
        title=heading.get_text(" ",strip=True)
        if not title or len(title)>180: continue
        container=heading.find_parent(["article","li","div","section"]) or heading.parent
        text=container.get_text(" ",strip=True) if container else ""
        start=_date(text)
        if not start: continue
        cls=classify(title,text,"Stand-up","Stand-up")
        city=""
        for c in ["Stockholm","Göteborg","Malmö","Örebro","Karlstad","Uppsala","Västerås","Linköping","Norrköping","Halmstad","Alingsås"]:
            if c.lower() in text.lower(): city=c; break
        link=heading.find("a") or (container.find("a") if container else None)
        href=link.get("href") if link else None
        if href and href.startswith("/"): href="https://showtic.se"+href
        ext=href or f"{title}-{start}-{city}"
        out.append(Event(id=f"showtic-{abs(hash(ext))}",title=title,event_type=cls.event_type,category=cls.category,start_date=start,end_date=start,start_time=None,venue="",city=city,region="",country="Sverige",official_url=href,ticket_url=href,status="confirmed",source_names=["Showtic"],source_count=1,source_records=[SourceRecord(source="Showtic",external_id=ext,source_url=href or url,fetched_at=_now(),raw_title=title)],verified_at=_now(),created_at=_now(),updated_at=_now(),description=text,tags=cls.tags,is_demo=False,data_quality="partial",quality_notes=["Showtic-import; experimentell parser"]))
    uniq={}
    for e in out: uniq[(e.title.lower(),e.start_date,e.city)]=e
    return list(uniq.values())

def experimental_entertainment_events(keys):
    events=[]; health=[]
    for key in keys or []:
        if key!="showtic": continue
        try:
            rows=showtic_standup_events(); events.extend(rows); health.append(("Showtic","OK (experimentell)",len(rows),"Stand-up/scen"))
        except Exception as exc: health.append(("Showtic","Fel",0,str(exc)))
    return events,health
